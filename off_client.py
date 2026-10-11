"""
Free, open product databases (no API keys):
- Open Food Facts, Open Beauty Facts, Open Pet Food Facts, Open Products Facts
  (same API: https://openfoodfacts.github.io/openfoodfacts-server/api/)
- Open Library for books (https://openlibrary.org/dev/docs/api/books)
"""
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

BARCODE_RE = re.compile(r"^\d{8,14}$")
_FIELDS = ",".join([
    "code", "product_name", "product_name_en", "brands", "ingredients_text", "ingredients_text_en",
    "image_front_url", "image_url", "nutriscore_grade", "nova_group", "ecoscore_grade",
    "nutriments", "allergens_tags", "categories_tags", "ingredients_analysis_tags", "additives_tags", "quantity",
])
USER_AGENT = os.environ.get("OPENFOODFACTS_USER_AGENT", "ScanBeforeUse/3.0 (student project)")
_IMAGE_HOST_RE = re.compile(r"^https://(images\.open(food|beauty|petfood|products)facts\.(org|net)|covers\.openlibrary\.org)/")

# key, host, display name
FOOD = ("food", "world.openfoodfacts.org", "Open Food Facts")
OTHER_DATABASES = [
    ("beauty", "world.openbeautyfacts.org", "Open Beauty Facts"),
    ("petfood", "world.openpetfoodfacts.org", "Open Pet Food Facts"),
    ("products", "world.openproductsfacts.org", "Open Products Facts"),
]


class LookupUnavailable(Exception):
    """A product database could not be reached."""


def valid_barcode(code: Any) -> Optional[str]:
    """Return the barcode as digits if it looks like an EAN/UPC, else None."""
    if not isinstance(code, (str, int)):
        return None
    code = re.sub(r"[\s-]", "", str(code))
    return code if BARCODE_RE.match(code) else None


def safe_image(url: Any) -> Optional[str]:
    """Only allow images from the databases' own image servers."""
    return url if isinstance(url, str) and _IMAGE_HOST_RE.match(url) else None


def _tags(p: Dict[str, Any], key: str) -> List[str]:
    return [t for t in p.get(key) or [] if isinstance(t, str)]


def fetch_product(barcode: str, host: str = FOOD[1]) -> Optional[Dict[str, Any]]:
    """Fetch a product by barcode. None if not found; LookupUnavailable on network error."""
    code = valid_barcode(barcode)
    if not code:
        return None
    url = f"https://{host}/api/v2/product/{code}.json"
    data = None
    for attempt in (1, 2):  # these free servers sometimes fail once under load
        try:
            resp = requests.get(url, params={"fields": _FIELDS}, headers={"User-Agent": USER_AGENT}, timeout=6)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            break
        except (requests.RequestException, ValueError) as exc:
            logger.warning("%s lookup failed for %s (try %d): %s", host, code, attempt, type(exc).__name__)
            if attempt == 2:
                raise LookupUnavailable() from exc
    if data.get("status") != 1 or not isinstance(data.get("product"), dict):
        return None
    p = data["product"]
    return {
        "barcode": code,
        "name": (p.get("product_name_en") or p.get("product_name") or "").strip() or None,
        "brand": (p.get("brands") or "").split(",")[0].strip() or None,
        "quantity": p["quantity"].strip() or None if isinstance(p.get("quantity"), str) else None,
        "ingredients_text": p.get("ingredients_text_en") or p.get("ingredients_text") or "",
        "image_url": safe_image(p.get("image_front_url") or p.get("image_url")),
        "nutriscore": (p.get("nutriscore_grade") or "").upper() if (p.get("nutriscore_grade") or "") in list("abcde") else None,
        "nova_group": p.get("nova_group") if p.get("nova_group") in (1, 2, 3, 4) else None,
        "ecoscore": (p.get("ecoscore_grade") or "").upper() if (p.get("ecoscore_grade") or "") in list("abcde") else None,
        "nutriments": p.get("nutriments") if isinstance(p.get("nutriments"), dict) else {},
        "allergens_tags": _tags(p, "allergens_tags"),
        "categories_tags": _tags(p, "categories_tags"),
        "analysis_tags": _tags(p, "ingredients_analysis_tags"),
        "additives_tags": _tags(p, "additives_tags"),
        "url": f"https://{host}/product/{code}",
    }


def fetch_other(barcode: str) -> Tuple[Optional[Tuple[str, str, Dict[str, Any]]], bool]:
    """Look a non-food product up in the beauty, pet food and general databases at once.
    Returns ((key, database name, product) or None, whether any database failed)."""
    def one(db):
        try:
            return db, fetch_product(barcode, db[1]), False
        except LookupUnavailable:
            return db, None, True

    with ThreadPoolExecutor(max_workers=len(OTHER_DATABASES)) as pool:
        results = list(pool.map(one, OTHER_DATABASES))
    failed = any(r[2] for r in results)
    for (key, _host, name), product, _ in results:  # keep the order above
        if product:
            return (key, name, product), failed
    return None, failed


def nice_tag(tag: str) -> str:
    """'en:hand-creams' -> 'Hand creams'."""
    text = tag.split(":", 1)[-1].replace("-", " ").strip()
    return text[:1].upper() + text[1:]


def fetch_book(isbn13: str) -> Optional[Dict[str, Any]]:
    """Book details from Open Library. None if not found; LookupUnavailable on network error."""
    key = f"ISBN:{isbn13}"
    try:
        resp = requests.get("https://openlibrary.org/api/books",
                            params={"bibkeys": key, "format": "json", "jscmd": "data"},
                            headers={"User-Agent": USER_AGENT}, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Open Library lookup failed for %s: %s", isbn13, type(exc).__name__)
        raise LookupUnavailable() from exc
    book = data.get(key) if isinstance(data, dict) else None
    if not isinstance(book, dict) or not book.get("title"):
        return None

    def names(field):
        return [x["name"] for x in book.get(field) or [] if isinstance(x, dict) and isinstance(x.get("name"), str)]

    cover = book.get("cover") if isinstance(book.get("cover"), dict) else {}
    link = book.get("url") if isinstance(book.get("url"), str) else None
    if link and link.startswith("http://openlibrary.org/"):
        link = "https://" + link[len("http://"):]
    return {
        "title": str(book["title"])[:300],
        "subtitle": book.get("subtitle") if isinstance(book.get("subtitle"), str) else None,
        "authors": names("authors"),
        "publishers": names("publishers"),
        "publish_date": book.get("publish_date") if isinstance(book.get("publish_date"), str) else None,
        "pages": book.get("number_of_pages") if isinstance(book.get("number_of_pages"), int) else None,
        "image_url": safe_image(cover.get("medium")),
        "url": link if link and link.startswith("https://openlibrary.org/") else None,
    }
