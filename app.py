"""
Food Product Scanner — Flask app (runs on Vercel, Docker or locally).

All configuration comes from environment variables; see .env.example.
The site stores no personal data: scan history lives in the visitor's own
browser, and the server keeps nothing between requests.
"""
import logging
import os
import threading
from datetime import date, datetime
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

import ai_label
import food_scanner
from nutriscore import NutriScoreCategory, calculate_nutri_score
from report_pdf import build_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")


def env_flag(name, default=False):
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")


app = Flask(__name__)
app.config.update(
    DEBUG=env_flag("FLASK_DEBUG", False),
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,   # Vercel rejects bodies over 4.5 MB anyway
    JSON_SORT_KEYS=False,
    SEND_FILE_MAX_AGE_DEFAULT=3600,     # cache CSS/JS/fonts for an hour
)
# Vercel and most hosts sit behind one proxy; trust it for client IP and HTTPS.
if env_flag("TRUST_PROXY", True):
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

SITE = {
    "name": os.environ.get("SITE_NAME", "Food Product Scanner"),
    "owner": os.environ.get("SITE_OWNER", "").strip(),
    "email": os.environ.get("CONTACT_EMAIL", "").strip(),
    "phone": os.environ.get("CONTACT_PHONE", "").strip(),
    "address": os.environ.get("BUSINESS_ADDRESS", "").strip(),
    "policy_date": "11 October 2026",
}
ALLOWED_ORIGINS = {o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()}

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    default_limits=["300 per hour"],
    headers_enabled=True,
)

# Best-effort daily cap on paid AI calls (per server instance). Also set a
# quota in Google Cloud for a hard limit.
AI_DAILY_LIMIT = int(os.environ.get("AI_DAILY_LIMIT", "200"))
_ai_usage = {"day": date.today(), "count": 0}
_ai_lock = threading.Lock()


def take_ai_slot() -> bool:
    with _ai_lock:
        if _ai_usage["day"] != date.today():
            _ai_usage.update(day=date.today(), count=0)
        if _ai_usage["count"] >= AI_DAILY_LIMIT:
            return False
        _ai_usage["count"] += 1
        return True

# --------------------------------------------------------------------------
# Request checks and security headers
# --------------------------------------------------------------------------
@app.before_request
def same_origin_for_api():
    """Block other websites from using the API through visitors' browsers.
    Requests with no Origin header (the mobile app, curl) are allowed."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("Origin")
        if origin and origin.rstrip("/") not in ALLOWED_ORIGINS:
            if urlparse(origin).netloc != request.host:
                abort(403)


@app.after_request
def security_headers(resp):
    csp = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob: https://images.openfoodfacts.org https://images.openfoodfacts.net; "
        "media-src 'self' blob:; font-src 'self'; connect-src 'self'; object-src 'none'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    resp.headers.setdefault("Content-Security-Policy", csp)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(), geolocation=(), payment=()")
    resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.path.startswith(("/scan", "/api/")):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.context_processor
def inject_site():
    return {"site": SITE, "current_year": datetime.now().year, "ai_enabled": ai_label.enabled()}

# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("scan.html")


@app.route("/dashboard")
def dashboard():  # old URL
    return redirect(url_for("index"), code=301)


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/nutri-score")
def nutri_score_page():
    return render_template("nutriscore.html")


@app.route("/privacy")
def privacy():
    return render_template("legal/privacy.html")


@app.route("/terms")
def terms():
    return render_template("legal/terms.html")


@app.route("/cookies")
def cookies():
    return render_template("legal/cookies.html")


@app.route("/refunds")
def refunds():
    return render_template("legal/refunds.html")


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /api/\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="img/favicon.svg"), code=301)

# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------
def scan_error(message, status):
    return jsonify({"success": False, "error": message}), status


@app.route("/scan", methods=["POST"])
@limiter.limit("30 per minute")
def scan():
    try:
        if "image" in request.files:
            return scan_photo()
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not data.get("barcode"):
            return scan_error("Send a barcode, or a photo in the 'image' field.", 400)
        return jsonify(food_scanner.scan_barcode(str(data.get("barcode"))[:32]))
    except food_scanner.ScanError as err:
        return scan_error(err.message, err.status)
    except HTTPException:
        raise  # rate limits, oversized uploads: handled by http_error
    except Exception:
        logger.exception("Scan failed")
        return scan_error("Something went wrong while scanning. Please try again.", 500)


def scan_photo():
    with limiter.limit("8 per minute; 60 per day", scope="scan-photo"):
        data = request.files["image"].read(app.config["MAX_CONTENT_LENGTH"] + 1)
        if not data:
            return scan_error("Choose a photo first.", 400)
        if not food_scanner.verify_image(data):
            return scan_error("That file isn't a JPEG, PNG or WebP photo.", 400)
        return jsonify(food_scanner.scan_image(data, allow_ai=take_ai_slot))


@app.route("/api/nutri-score/calculate", methods=["POST"])
@limiter.limit("60 per minute")
def api_nutri_score():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = request.form.to_dict()

    def num(key, hi):
        try:
            v = float(data.get(key) or 0)
        except (TypeError, ValueError):
            raise ValueError(key)
        if not 0 <= v <= hi:
            raise ValueError(key)
        return v

    try:
        category = NutriScoreCategory(data.get("category") or "general_foods")
    except ValueError:
        return scan_error("Unknown food category.", 400)
    try:
        energy = num("energy_kj", 4000) if data.get("energy_unit", "kj") == "kj" else num("energy_kj", 1000) * 4.184
        result = calculate_nutri_score(
            energy_kj=energy, sat_fat=num("sat_fat", 100), sugars=num("sugars", 100), salt=num("salt", 100),
            fiber=num("fiber", 100), protein=num("protein", 100), fruit_veg_percentage=num("fruit_veg_percentage", 100),
            fat=num("fat", 100) if data.get("fat") not in (None, "") else None, category=category,
            has_non_nutritive_sweeteners=str(data.get("sweeteners", "")).lower() in ("1", "true", "yes", "on"),
        )
    except ValueError as bad:
        return scan_error(f"Check the value for {str(bad).replace('_', ' ')}: it must be a number within a sensible range.", 400)
    return jsonify({"success": True, "result": result})


@app.route("/api/report/pdf", methods=["POST"])
@limiter.limit("20 per minute")
def api_report_pdf():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("dashboard"), dict):
        return scan_error("No scan result to turn into a report.", 400)
    pdf = build_pdf(data, SITE["name"])
    name = "".join(c if c.isalnum() else "_" for c in str(data["dashboard"].get("Product Name", "product")))[:60] or "product"
    return send_file(__import__("io").BytesIO(pdf), mimetype="application/pdf",
                     as_attachment=True, download_name=f"{name}_report.pdf")

# --------------------------------------------------------------------------
# Errors: friendly pages for people, JSON for the API. Never leak internals.
# --------------------------------------------------------------------------
MESSAGES = {
    400: ("Bad request", "Something about that request wasn't right."),
    403: ("Not allowed", "That request isn't allowed from here."),
    404: ("Page not found", "That page doesn't exist or has moved."),
    405: ("Not allowed", "That action isn't supported here."),
    413: ("Too large", "That photo is too big. Please use one under 4 MB."),
    429: ("Slow down", "Too many requests. Please wait a minute and try again."),
    500: ("Something went wrong", "Please try again in a moment."),
}


@app.errorhandler(HTTPException)
def http_error(err):
    title, message = MESSAGES.get(err.code, (err.name, "Please try again."))
    if request.path.startswith(("/scan", "/api/")):
        return scan_error(message, err.code)
    return render_template("error.html", code=err.code, title=title, message=message), err.code


@app.errorhandler(Exception)
def unhandled(_err):
    logger.exception("Unhandled error")
    title, message = MESSAGES[500]
    if request.path.startswith(("/scan", "/api/")):
        return scan_error(message, 500)
    return render_template("error.html", code=500, title=title, message=message), 500


if __name__ == "__main__":
    # Local development only:  FLASK_DEBUG=1 python app.py
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)),
            debug=app.config["DEBUG"])
