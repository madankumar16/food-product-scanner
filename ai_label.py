"""
Optional label reading with Google Gemini.

Only used when GEMINI_API_KEY is set. The key is sent in a request header
(never in the URL, so it can't leak into logs). If anything fails we return
None — we never invent a product.
"""
import base64
import io
import json
import logging
import os
from typing import Any, Dict, Optional

import requests
from PIL import Image

logger = logging.getLogger(__name__)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

PROMPT = """You read food packaging photos. Reply with JSON only, using exactly these keys:
{"is_food_label": true|false,
 "product_name": string or null,
 "brand": string or null,
 "barcode": digits or null,
 "ingredients_text": the ingredients list copied exactly as printed, or null,
 "veg_mark": "green" | "brown" | "none" (Indian FSSAI veg/non-veg symbol),
 "allergens_declared": [strings printed in any "contains"/allergen statement],
 "legible": true|false}
Copy only text you can actually read. Use null when something is not visible. Never guess."""


def enabled() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def _prepare(image_bytes: bytes) -> str:
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img.thumbnail((1600, 1600))  # labels stay readable; uploads stay small and cheap
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def read_label(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()
    body = {
        "contents": [{"parts": [{"text": PROMPT},
                                {"inline_data": {"mime_type": "image/jpeg", "data": _prepare(image_bytes)}}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 2048, "responseMimeType": "application/json"},
    }
    try:
        resp = requests.post(API_URL.format(model=model), json=body, timeout=45,
                             headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    except requests.RequestException as exc:
        logger.warning("Gemini request failed: %s", type(exc).__name__)
        return None
    if resp.status_code != 200:
        logger.warning("Gemini returned HTTP %s", resp.status_code)  # body not logged
        return None
    try:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
    except (KeyError, IndexError, TypeError, ValueError):
        logger.warning("Gemini reply could not be parsed")
        return None
    if not isinstance(data, dict) or not data.get("is_food_label") or not data.get("legible"):
        return None

    def s(v, n=300):
        return v.strip()[:n] if isinstance(v, str) and v.strip() else None

    mark = data.get("veg_mark")
    return {
        "name": s(data.get("product_name"), 150),
        "brand": s(data.get("brand"), 100),
        "barcode": s(data.get("barcode"), 20),
        "ingredients_text": s(data.get("ingredients_text"), 4000) or "",
        "veg_mark": mark if mark in ("green", "brown") else None,
        "allergens_declared": [s(a, 60) for a in data.get("allergens_declared") or [] if s(a, 60)][:20],
    }
