"""Open Food Facts lookup (free, no API key). https://world.openfoodfacts.org"""
import logging
import os
import re
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

BARCODE_RE = re.compile(r"^\d{8,14}$")
_FIELDS = ",".join([
    "code", "product_name", "product_name_en", "brands", "ingredients_text", "ingredients_text_en",
    "image_front_url", "image_url", "nutriscore_grade", "nova_group", "ecoscore_grade",
    "nutriments", "allergens_tags", "categories_tags", "ingredients_analysis_tags", "additives_tags",
])
USER_AGENT = os.environ.get("OPENFOODFACTS_USER_AGENT", "FoodProductScanner/2.0 (student project)")
_IMAGE_HOST_RE = re.compile(r"^https://images\.openfoodfacts\.(org|net)/")


def valid_barcode(code: Any) -> Optional[str]:
    """Return the barcode as digits if it looks like an EAN/UPC, else None."""
    if not isinstance(code, (str, int)):
        return None
    code = re.sub(r"[\s-]", "", str(code))
    return code if BARCODE_RE.match(code) else None


def fetch_product(barcode: str) -> Optional[Dict[str, Any]]:
    """Fetch a product by barcode. Returns None if not found or on network error."""
    code = valid_barcode(barcode)
    if not code:
        return None
    url = f"https://world.openfoodfacts.org/api/v2/product/{code}.json"
    try:
        resp = requests.get(url, params={"fields": _FIELDS}, headers={"User-Agent": USER_AGENT}, timeout=8)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Open Food Facts lookup failed for %s: %s", code, type(exc).__name__)
        raise LookupUnavailable() from exc
    if data.get("status") != 1 or not isinstance(data.get("product"), dict):
        return None
    p = data["product"]
    image = p.get("image_front_url") or p.get("image_url")
    return {
        "barcode": code,
        "name": (p.get("product_name_en") or p.get("product_name") or "").strip() or None,
        "brand": (p.get("brands") or "").split(",")[0].strip() or None,
        "ingredients_text": p.get("ingredients_text_en") or p.get("ingredients_text") or "",
        # Only allow images from Open Food Facts' own image server
        "image_url": image if isinstance(image, str) and _IMAGE_HOST_RE.match(image) else None,
        "nutriscore": (p.get("nutriscore_grade") or "").upper() if (p.get("nutriscore_grade") or "") in list("abcde") else None,
        "nova_group": p.get("nova_group") if p.get("nova_group") in (1, 2, 3, 4) else None,
        "ecoscore": (p.get("ecoscore_grade") or "").upper() if (p.get("ecoscore_grade") or "") in list("abcde") else None,
        "nutriments": p.get("nutriments") if isinstance(p.get("nutriments"), dict) else {},
        "allergens_tags": [t for t in p.get("allergens_tags") or [] if isinstance(t, str)],
        "categories_tags": [t for t in p.get("categories_tags") or [] if isinstance(t, str)],
        "analysis_tags": [t for t in p.get("ingredients_analysis_tags") or [] if isinstance(t, str)],
        "additives_tags": [t for t in p.get("additives_tags") or [] if isinstance(t, str)],
    }


class LookupUnavailable(Exception):
    """Open Food Facts could not be reached."""
