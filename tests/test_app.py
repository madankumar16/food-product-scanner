"""Tests for the Food Product Scanner. Network calls are mocked. Run: pytest -q"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT))
os.environ.pop("GEMINI_API_KEY", None)

import analysis  # noqa: E402
import codes  # noqa: E402
import app as webapp  # noqa: E402
import nutriscore as ns  # noqa: E402
import off_client  # noqa: E402

PRODUCT = {
    "status": 1,
    "product": {
        "product_name": "Masala Noodles", "brands": "TestBrand, Other",
        "ingredients_text": "Wheat flour (maida), palm oil, salt, sugar, spices (chilli, turmeric), flavour enhancer (E621)",
        "image_front_url": "https://images.openfoodfacts.org/images/products/890/front.jpg",
        "nutriscore_grade": "d", "nova_group": 4,
        "nutriments": {"energy-kj_100g": 1800, "saturated-fat_100g": 7.5, "sugars_100g": 2.5, "salt_100g": 3.1,
                       "fiber_100g": 2.0, "proteins_100g": 8.0, "fat_100g": 15.0},
        "categories_tags": ["en:noodles"], "ingredients_analysis_tags": ["en:vegetarian"], "allergens_tags": ["en:gluten"],
    },
}


class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


@pytest.fixture()
def client():
    webapp.limiter.reset()
    with webapp.app.test_client() as c:
        yield c


def off_returns(payload=PRODUCT, status=200):
    return mock.patch("off_client.requests.get", return_value=FakeResp(status, payload))


# ---------------- configuration and secrets ----------------
def test_debug_is_off_by_default():
    assert webapp.app.debug is False


def test_no_secrets_or_default_accounts_in_repo():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    for name in tracked:
        path = ROOT / name
        if path == Path(__file__).resolve():
            continue  # this file contains the patterns it searches for
        if path.suffix in (".py", ".md", ".txt", ".html", ".js", ".json", ".yml", ".sh", ".bat", ".example") and path.exists():
            text = path.read_text(errors="ignore")
            assert not re.search(r"AIza[0-9A-Za-z_\-]{35}", text), name
            assert "admin123" not in text, name


def test_security_headers(client):
    h = client.get("/").headers
    assert "script-src 'self'" in h["Content-Security-Policy"]
    assert h["X-Frame-Options"] == "DENY"
    assert h["X-Content-Type-Options"] == "nosniff"
    assert "camera=(self)" in h["Permissions-Policy"]
    assert "Set-Cookie" not in h  # the site uses no cookies


# ---------------- pages ----------------
@pytest.mark.parametrize("path", ["/", "/history", "/nutri-score", "/privacy", "/terms", "/cookies", "/refunds"])
def test_pages_have_title_description_favicon(client, path):
    r = client.get(path)
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert re.search(r"<title>[^<]{8,}</title>", html)
    assert re.search(r'<meta name="description" content="[^"]{20,}"', html)
    assert 'rel="icon"' in html
    assert "unpkg.com" not in html and "googleapis" not in html


def test_nav_has_at_most_five_links(client):
    html = client.get("/").get_data(as_text=True)
    nav = html.split('id="nav-links"')[1].split("</ul>")[0]
    assert nav.count("<a ") <= 5


def test_custom_404_and_removed_endpoints(client):
    r = client.get("/nope")
    assert r.status_code == 404 and "Page not found" in r.get_data(as_text=True)
    for gone in ["/test/scanner", "/api/history", "/profile", "/api/scan/1", "/download/pdf/1", "/scan/1"]:
        assert client.get(gone).status_code in (404, 405), gone


def test_old_dashboard_url_redirects(client):
    assert client.get("/dashboard").status_code == 301


# ---------------- barcode scanning ----------------
def test_barcode_scan_returns_real_data_in_mobile_app_shape(client):
    with off_returns() as get:
        r = client.post("/scan", json={"type": "barcode", "barcode": "8901058000290"})
    data = r.get_json()
    assert r.status_code == 200 and data["success"] is True
    d = data["dashboard"]
    assert data["result"] == d                                   # old web clients
    assert d["Product Name"] == "Masala Noodles" and d["Brand"] == "TestBrand"
    assert isinstance(d["Safety Score"], int)                     # Flutter reads it as int
    assert "Gluten (wheat, barley, rye)" in d["Allergens"]
    assert "Palm oil (high in saturated fat)" in d["Flags"]
    assert data["open_food_facts"]["nutriscore"] in list("ABCDE")
    assert data["open_food_facts"]["image_url"].startswith("https://images.openfoodfacts.org/")
    assert "8901058000290.json" in get.call_args[0][0]


def test_unknown_product_is_reported_not_faked(client):
    with off_returns({"status": 0}) as get:
        r = client.post("/scan", json={"barcode": "1234567890128"})
    data = r.get_json()
    assert r.status_code == 200 and data["kind"] == "code"
    assert "dashboard" not in data                      # no veg status or scores for an unknown item
    assert "isn't in Open Food Facts, Open Beauty Facts" in data["notes"][0]
    assert ["Check digit", "Valid"] in data["code"]["facts"]
    assert get.call_count == 4                          # food, beauty, pet food, products
    body = json.dumps(data)
    for fake in ("Smart Cola", "Water", "Natural Flavors", "SmartBrand", "Vegetarian"):
        assert fake not in body


def test_database_down_gives_503(client):
    import requests
    with mock.patch("off_client.requests.get", side_effect=requests.ConnectionError()):
        r = client.post("/scan", json={"barcode": "8901058000290"})
    assert r.status_code == 503


@pytest.mark.parametrize("bad", ["", "   ", None, ["x"], "x" * 5000])
def test_empty_or_oversized_codes_rejected(client, bad):
    with off_returns() as get:
        r = client.post("/scan", json={"code": bad})
    assert r.status_code == 400
    assert get.call_count == 0


@pytest.mark.parametrize("text", ["12", "abc12345", "<script>alert(1)</script>", "1" * 20, "../../etc/passwd"])
def test_non_product_codes_are_decoded_not_looked_up(client, text):
    with off_returns() as get:
        r = client.post("/scan", json={"code": text, "format": "CODE_128"})
    data = r.get_json()
    assert r.status_code == 200 and data["kind"] == "code"
    assert get.call_count == 0
    assert data["code"]["text"] == text                 # shown as text by the page, never as HTML


def test_product_number_with_wrong_check_digit_is_not_looked_up(client):
    with off_returns() as get:
        data = client.post("/scan", json={"code": "8901058000291"}).get_json()
    assert get.call_count == 0 and data["title"] == "Number"
    assert "last digit doesn't match" in data["notes"][0]


def test_non_food_product_comes_from_its_own_database(client):
    beauty = {"status": 1, "product": {"product_name": "Hand cream", "brands": "Brand", "quantity": "75 ml",
              "categories_tags": ["en:creams"], "image_front_url": "https://images.openbeautyfacts.org/x.jpg"}}

    def fake_get(url, **kw):
        return FakeResp(200, beauty if "openbeautyfacts" in url else {"status": 0})

    with mock.patch("off_client.requests.get", side_effect=fake_get):
        data = client.post("/scan", json={"code": "8410757001090", "format": "EAN_13"}).get_json()
    assert data["kind"] == "product" and data["source"] == "open_beauty_facts"
    assert data["item"]["database"] == "Open Beauty Facts" and data["item"]["title"] == "Hand cream"
    assert ["Quantity", "75 ml"] in data["item"]["facts"]
    assert data["item"]["image_url"].startswith("https://images.openbeautyfacts.org/")
    assert ["Scanned as", "EAN-13"] in data["code"]["facts"]


def test_isbn_is_looked_up_in_open_library(client):
    book = {"ISBN:9780140449136": {"title": "Crime and punishment", "authors": [{"name": "F. Dostoevsky"}],
                                   "publishers": [{"name": "Penguin"}], "publish_date": "2003", "number_of_pages": 671,
                                   "url": "http://openlibrary.org/books/OL1M/x", "cover": {"medium": "https://covers.openlibrary.org/b/id/1-M.jpg"}}}
    with mock.patch("off_client.requests.get", return_value=FakeResp(200, book)) as get:
        data = client.post("/scan", json={"code": "0140449132"}).get_json()   # ISBN-10 is converted
    assert data["kind"] == "book" and data["item"]["title"] == "Crime and punishment"
    assert ["Pages", "671"] in data["item"]["facts"]
    assert data["item"]["url"].startswith("https://openlibrary.org/")
    assert "openlibrary.org" in get.call_args[0][0]


def test_store_internal_codes_are_explained_not_looked_up(client):
    code = next(c for c in ("20012340000" + str(d) + "0" for d in range(10)) if codes.gtin_check_ok(c[:12] + c[12]))
    with off_returns() as get:
        data = client.post("/scan", json={"code": code}).get_json()
    assert get.call_count == 0 and "shop's own number" in data["notes"][0]


def test_gs1_datamatrix_shows_expiry_and_warns_when_expired(client):
    with off_returns():
        data = client.post("/scan", json={"code": "(01)08901058000290(17)240131(10)AB12", "format": "DATA_MATRIX"}).get_json()
    facts = data["code"]["facts"]
    assert ["Expiry date", "31 Jan 2024"] in facts and ["Batch / lot", "AB12"] in facts
    assert data["warning"].startswith("Expired on 31 Jan 2024")
    assert data["kind"] == "food"                       # the product number was looked up too


@pytest.mark.parametrize("text,title,fact", [
    ("upi://pay?pa=shop@okaxis&pn=Ravi%20Stores&am=150&cu=INR", "UPI payment request", ["Pay to (UPI ID)", "shop@okaxis"]),
    ("WIFI:T:WPA;S:Home Net;P:pa\\;ss;;", "Wi-Fi network", ["Password", "pa;ss"]),
    ("https://example.com/menu", "Web link", ["Website", "example.com"]),
    ("BEGIN:VCARD\nFN:Asha Rao\nTEL:+919876543210\nEND:VCARD", "Contact card", ["Phone", "+919876543210"]),
    ("mailto:help@example.com?subject=Hi", "Email", ["Subject", "Hi"]),
    ("tel:+911234567890", "Phone number", ["Number", "+911234567890"]),
    ("SMSTO:+911234567890:Hello", "Text message", ["Message", "Hello"]),
    ("geo:12.97,77.59", "Map location", ["Latitude", "12.97"]),
    ("hello world", "Text", ["Text", "hello world"]),
])
def test_qr_contents_are_decoded(client, text, title, fact):
    data = client.post("/scan", json={"code": text, "format": "QR_CODE"}).get_json()
    assert data["title"] == title and fact in data["content"]["facts"]


def test_upi_and_links_carry_warnings(client):
    upi = client.post("/scan", json={"code": "upi://pay?pa=a@b"}).get_json()
    plain = client.post("/scan", json={"code": "http://example.com"}).get_json()
    assert "never gives you money" in upi["warning"]
    assert "not secure" in plain["warning"]


def test_gs1_digital_link_is_looked_up(client):
    with off_returns() as get:
        data = client.post("/scan", json={"code": "https://id.gs1.org/01/08901058000290"}).get_json()
    assert data["kind"] == "food" and "8901058000290.json" in get.call_args[0][0]


def test_upce_is_expanded():
    assert codes.upce_to_upca("04252614") == "042100005264"
    assert codes.describe_gtin("04252614", "UPC-E")["lookup"] == "0042100005264"


def test_errors_never_leak_tracebacks(client):
    with mock.patch("food_scanner.scan_code", side_effect=RuntimeError("secret internal detail")):
        r = client.post("/scan", json={"barcode": "8901058000290"})
    assert r.status_code == 500
    assert "secret internal detail" not in r.get_data(as_text=True)
    assert "Traceback" not in r.get_data(as_text=True)


def test_untrusted_image_hosts_are_dropped():
    p = json.loads(json.dumps(PRODUCT))
    p["product"]["image_front_url"] = "javascript:alert(1)"
    with off_returns(p):
        assert off_client.fetch_product("8901058000290")["image_url"] is None


# ---------------- photos ----------------
def test_photo_with_barcode_is_decoded(client):
    with off_returns() as get, open(FIX / "barcode.png", "rb") as fh:
        r = client.post("/scan", data={"image": (fh, "photo.png")}, content_type="multipart/form-data")
    assert r.status_code == 200, r.get_json()
    assert "8901058000290.json" in get.call_args[0][0]


def test_photo_without_barcode_and_no_ai_is_honest(client):
    with open(FIX / "blank.jpg", "rb") as fh:
        r = client.post("/scan", data={"image": (fh, "photo.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 422
    assert "No barcode or QR code found" in r.get_json()["error"]


def test_non_image_upload_rejected(client):
    import io
    r = client.post("/scan", data={"image": (io.BytesIO(b"<?php system($_GET['x']); ?>"), "shell.php.jpg")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_oversized_upload_rejected(client):
    import io
    r = client.post("/scan", data={"image": (io.BytesIO(b"0" * (5 * 1024 * 1024)), "big.jpg")},
                    content_type="multipart/form-data")
    assert r.status_code == 413


def test_ai_label_reading_sends_key_in_header_only(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    reply = {"candidates": [{"content": {"parts": [{"text": json.dumps({
        "is_food_label": True, "legible": True, "product_name": "Chicken Soup", "brand": "B",
        "barcode": None, "ingredients_text": "Water, chicken, salt", "veg_mark": "brown", "allergens_declared": []})}]}}]}
    with mock.patch("ai_label.requests.post", return_value=FakeResp(200, reply)) as post, open(FIX / "blank.jpg", "rb") as fh:
        r = client.post("/scan", data={"image": (fh, "label.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 200
    data = r.get_json()
    assert data["source"] == "label_photo"
    assert data["dashboard"]["Veg Status"] == "Non-Vegetarian"
    url = post.call_args[0][0]
    assert "test-key-not-real" not in url
    assert post.call_args[1]["headers"]["x-goog-api-key"] == "test-key-not-real"


def test_ai_failure_is_honest(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    with mock.patch("ai_label.requests.post", return_value=FakeResp(500, {})), open(FIX / "blank.jpg", "rb") as fh:
        r = client.post("/scan", data={"image": (fh, "label.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 422
    assert "couldn't read that label" in r.get_json()["error"]


def test_ai_daily_cap(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(webapp, "AI_DAILY_LIMIT", 0)
    with mock.patch("ai_label.requests.post") as post, open(FIX / "blank.jpg", "rb") as fh:
        r = client.post("/scan", data={"image": (fh, "label.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 429 and post.call_count == 0


# ---------------- abuse protection ----------------
def test_cross_site_requests_blocked(client):
    with off_returns():
        evil = client.post("/scan", json={"barcode": "8901058000290"}, headers={"Origin": "https://evil.example"})
        same = client.post("/scan", json={"barcode": "8901058000290"}, headers={"Origin": "http://localhost"})
        app_ = client.post("/scan", json={"barcode": "8901058000290"})  # mobile app sends no Origin
    assert evil.status_code == 403
    assert same.status_code == 200 and app_.status_code == 200


def test_scan_rate_limited(client):
    with off_returns():
        codes = [client.post("/scan", json={"barcode": "8901058000290"}).status_code for _ in range(32)]
    assert codes[0] == 200 and 429 in codes


def test_static_urls_are_versioned_and_cacheable(client):
    html = client.get("/").get_data(as_text=True)
    assets = re.findall(r'(?:href|src)="(/static/[^"]+)"', html)
    assert assets and all(re.search(r"\?v=[0-9a-f]{10}$", a) for a in assets)
    resp = client.get(assets[0])
    assert resp.status_code == 200
    assert "immutable" in resp.headers["Cache-Control"]


def test_error_responses_are_never_cached(client):
    resp = client.get("/static/css/missing.css")
    assert resp.status_code == 404
    assert resp.headers["Cache-Control"] == "no-store"


def test_photo_rate_limited(client):
    codes = []
    for _ in range(10):
        with open(FIX / "blank.jpg", "rb") as fh:
            codes.append(client.post("/scan", data={"image": (fh, "p.jpg")}, content_type="multipart/form-data").status_code)
    assert 429 in codes


# ---------------- PDF ----------------
def test_pdf_report_is_stateless_and_escapes_text(client):
    with off_returns():
        data = client.post("/scan", json={"barcode": "8901058000290"}).get_json()
    data["dashboard"]["Product Name"] = "<b>Bold & <i>broken</b> markup"
    r = client.post("/api/report/pdf", json=data)
    assert r.status_code == 200 and r.data.startswith(b"%PDF")
    assert client.post("/api/report/pdf", json={"nope": 1}).status_code == 400


# ---------------- Nutri-Score ----------------
def test_nutriscore_api_validates(client):
    ok = client.post("/api/nutri-score/calculate", json={"category": "general_foods", "energy_unit": "kj",
                     "energy_kj": 2252, "sat_fat": 10.6, "sugars": 56.3, "salt": 0.107, "protein": 6.3})
    assert ok.get_json()["result"]["letter"] == "E"
    assert client.post("/api/nutri-score/calculate", json={"energy_kj": -5}).status_code == 400
    assert client.post("/api/nutri-score/calculate", json={"sugars": "lots"}).status_code == 400
    assert client.post("/api/nutri-score/calculate", json={"category": "pizza"}).status_code == 400


@pytest.mark.parametrize("name,kw,cat,expected", [
    ("Nutella", dict(energy_kj=2252, sat_fat=10.6, sugars=56.3, salt=0.107, protein=6.3), "GENERAL_FOODS", "E"),
    ("Rolled oats", dict(energy_kj=1450, sat_fat=0.3, sugars=1, salt=0.02, fiber=10, protein=13), "GENERAL_FOODS", "A"),
    ("Cola", dict(energy_kj=180, sat_fat=0, sugars=10.6, salt=0), "BEVERAGE", "E"),
    ("Diet cola", dict(energy_kj=1.3, sat_fat=0, sugars=0, salt=0.02, has_non_nutritive_sweeteners=True), "BEVERAGE", "C"),
    ("Olive oil", dict(energy_kj=3700, sat_fat=14, fat=100, sugars=0, salt=0, fruit_veg_percentage=100), "FATS_OILS_NUTS", "B"),
    ("Butter", dict(energy_kj=3050, sat_fat=54, fat=82, sugars=0.6, salt=0.02), "FATS_OILS_NUTS", "E"),
])
def test_nutriscore_known_products(name, kw, cat, expected):
    assert ns.calculate_nutri_score(category=ns.NutriScoreCategory[cat], **kw)["letter"] == expected, name


def test_category_mapping_no_false_matches():
    assert ns.map_to_nutriscore_category(["en:low-fat-yogurts"]) == ns.NutriScoreCategory.GENERAL_FOODS
    assert ns.map_to_nutriscore_category([], "Nutella hazelnut spread") == ns.NutriScoreCategory.GENERAL_FOODS
    assert ns.map_to_nutriscore_category([], "Coconut cookies") == ns.NutriScoreCategory.GENERAL_FOODS
    assert ns.map_to_nutriscore_category(["en:sodas"]) == ns.NutriScoreCategory.BEVERAGE


# ---------------- vegetarian status ----------------
@pytest.mark.parametrize("ingredients,tags,mark,expected", [
    (["Chicken", "Salt"], ["en:vegetarian"], None, "Non-Vegetarian"),     # ingredients beat wrong tags
    (["Wheat flour", "Egg", "Sugar"], [], None, "Non-Vegetarian"),       # egg = non-veg in India
    (["Gelatine", "Sugar"], [], None, "Non-Vegetarian"),
    (["Eggplant", "Oil"], [], None, "Not confirmed"),                    # not an egg
    (["Coconut milk", "Peanut butter"], [], None, "Not confirmed"),
    (["Rice", "Dal"], ["en:vegetarian"], None, "Vegetarian"),
    (["Rice", "Dal"], [], "green", "Vegetarian"),
    (["Rice"], [], "brown", "Non-Vegetarian"),
    ([], [], None, "Not confirmed"),                                    # never defaults to Vegetarian
])
def test_veg_status(ingredients, tags, mark, expected):
    assert analysis.veg_status(ingredients, tags, mark)["status"] == expected


def test_no_ingredients_means_no_score():
    assert analysis.ingredient_score([])["score"] is None


def test_split_ingredients_keeps_brackets():
    assert analysis.split_ingredients("Ingredients: Flour (wheat, salt), Sugar; Oil.") == ["Flour (wheat, salt)", "Sugar", "Oil"]
