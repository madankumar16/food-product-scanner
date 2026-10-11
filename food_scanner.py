"""
Scan pipeline: any barcode or QR code in, an honest description out.

1. Product barcode -> Open Food Facts; if not food, Open Beauty / Pet Food /
   Products Facts; books (ISBN) -> Open Library
2. GS1 codes on medicines and fresh food -> product number, expiry, batch
3. Any other code (links, UPI, Wi-Fi, contacts...) -> decoded from the code itself
4. Photo -> read any barcode with zxing-cpp; if none and GEMINI_API_KEY is set,
   read the ingredients label with Gemini
Anything we can't identify is reported as such. We never substitute sample or
placeholder products.
"""
import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import ai_label
import analysis
import codes
import off_client
from nutriscore import calculate_nutri_score_safe

logger = logging.getLogger(__name__)


class ScanError(Exception):
    """A scan that couldn't produce a result. `message` is safe to show users."""

    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.message = message
        self.status = status


def decode_barcode(image_bytes: bytes) -> Optional[Tuple[str, str]]:
    """Find any barcode or QR code in a photo (zxing-cpp; no system libraries needed).
    Returns (text, format name), preferring product barcodes when there are several."""
    try:
        import zxingcpp
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img).convert("L")
            img.thumbnail((2000, 2000))
            found = [(r.text, r.format.name) for r in zxingcpp.read_barcodes(img) if r.text]
    except Exception:
        logger.warning("Barcode decoding failed", exc_info=False)
        return None
    found.sort(key=lambda f: not codes.gtin_check_ok(re.sub(r"\D", "", f[0])))
    return found[0] if found else None


def _nutriscore_from(product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    n = product.get("nutriments") or {}

    def g(*keys):
        for k in keys:
            v = n.get(k)
            if isinstance(v, (int, float)):
                return float(v)
        return None

    energy = g("energy-kj_100g", "energy_100g")
    if energy is None and g("energy-kcal_100g") is not None:
        energy = g("energy-kcal_100g") * 4.184
    core = [energy, g("saturated-fat_100g"), g("sugars_100g"), g("salt_100g")]
    if any(v is None for v in core):
        return None  # not enough nutrition data to calculate honestly
    return calculate_nutri_score_safe(
        energy_kj=energy, sat_fat=core[1], sugars=core[2], salt=core[3],
        fiber=g("fiber_100g"), protein=g("proteins_100g"), fat=g("fat_100g"),
        fruit_veg_percentage=g("fruits-vegetables-legumes-estimate-from-ingredients_100g",
                               "fruits-vegetables-nuts-estimate-from-ingredients_100g"),
        categories_tags=product.get("categories_tags"), product_name=product.get("name") or "",
        has_non_nutritive_sweeteners=any(t in (product.get("additives_tags") or [])
                                         for t in ("en:e950", "en:e951", "en:e952", "en:e954", "en:e955", "en:e960", "en:e961", "en:e962")),
    )


def build_result(product: Dict[str, Any], source: str, label_mark: Optional[str] = None,
                 declared_allergens=None, code: Optional[Dict[str, Any]] = None,
                 warning: Optional[str] = None) -> Dict[str, Any]:
    ingredients = analysis.split_ingredients(product.get("ingredients_text"))
    veg = analysis.veg_status(ingredients, product.get("analysis_tags"), label_mark)
    allergens = analysis.allergens(ingredients, (product.get("allergens_tags") or []) + list(declared_allergens or []))
    score = analysis.ingredient_score(ingredients)
    calc = _nutriscore_from(product)

    warnings = [{"ingredient": a, "conditions": ["Allergen"], "severity": "Allergen"} for a in allergens]
    warnings += [{"ingredient": f, "conditions": ["Limit intake"], "severity": "Caution"} for f in score["flags"]]

    dashboard = {
        "Product Name": product.get("name") or "Name not available",
        "Brand": product.get("brand") or "Brand not available",
        "Veg Status": veg["status"],
        "Veg Reason": veg["reason"],
        "Safety Color": score["band"],          # kept for the mobile app; shown as "Ingredient score"
        "Safety Score": score["score"],
        "Ingredients": ingredients,
        "Allergens": allergens,
        "Flags": score["flags"],
        "Health Warnings": warnings,
    }
    nutriscore_letter = (calc or {}).get("letter") or product.get("nutriscore")
    return {
        "success": True,
        "kind": "food",
        "title": dashboard["Product Name"],
        "source": source,
        "code": code,
        "warning": warning,
        "dashboard": dashboard,
        "result": dashboard,                       # older clients read "result"
        "open_food_facts": {
            "barcode": product.get("barcode"),
            "image_url": product.get("image_url"),
            "nutriscore": nutriscore_letter,
            "nutriscore_calculated": calc,
            "nutriscore_category": (calc or {}).get("mapped_category"),
            "nova_group": product.get("nova_group"),
            "ecoscore": product.get("ecoscore"),
            "nutriments": _public_nutriments(product.get("nutriments") or {}),
            "allergens": allergens,
        },
        "ai_analysis": {},
        "notes": [] if ingredients else ["No ingredients list was available for this product."],
    }


_NUTRIMENT_KEYS = ("energy-kcal_100g", "energy-kj_100g", "fat_100g", "saturated-fat_100g", "carbohydrates_100g",
                   "sugars_100g", "fiber_100g", "proteins_100g", "salt_100g", "sodium_100g")


def _public_nutriments(n: Dict[str, Any]) -> Dict[str, float]:
    return {k: float(n[k]) for k in _NUTRIMENT_KEYS if isinstance(n.get(k), (int, float))}


_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1c\x1e\x1f\x7f]")  # keeps tab, newlines and GS (\x1d)
_NOT_FOUND = "Open Food Facts, Open Beauty Facts, Open Pet Food Facts or Open Products Facts"


def _result(kind: str, title: str, source: str, code: Dict[str, Any], *, item=None, content=None,
            warning=None, notes: Optional[List[str]] = None) -> Dict[str, Any]:
    return {"success": True, "kind": kind, "title": title, "source": source, "code": code,
            "item": item, "content": content, "warning": warning, "notes": notes or []}


def _product_item(product: Dict[str, Any], database: str) -> Dict[str, Any]:
    facts = [["Brand", product.get("brand")], ["Quantity", product.get("quantity")]]
    cats = [off_client.nice_tag(t) for t in (product.get("categories_tags") or [])[-3:]]
    if cats:
        facts.append(["Category", ", ".join(cats)])
    sections = [["Ingredients", product["ingredients_text"]]] if product.get("ingredients_text") else []
    return {"title": product.get("name") or "Name not available", "subtitle": product.get("brand"),
            "image_url": product.get("image_url"), "facts": [f for f in facts if f[1]], "sections": sections,
            "database": database, "url": product.get("url")}


def _book_item(book: Dict[str, Any]) -> Dict[str, Any]:
    facts = [["Author", ", ".join(book["authors"])], ["Publisher", ", ".join(book["publishers"])],
             ["Published", book.get("publish_date")], ["Pages", str(book["pages"]) if book.get("pages") else None]]
    title = book["title"] + (f": {book['subtitle']}" if book.get("subtitle") else "")
    return {"title": title, "subtitle": ", ".join(book["authors"]) or None, "image_url": book.get("image_url"),
            "facts": [f for f in facts if f[1]], "sections": [], "database": "Open Library", "url": book.get("url")}


def _lookup_gtin(info: Dict[str, Any], code: Dict[str, Any], warning: Optional[str]) -> Dict[str, Any]:
    number = info["lookup"]
    label = f"Barcode {info['gtin']}"
    if info["is_restricted"]:
        return _result("code", label, "barcode", code, warning=warning, notes=[
            "This is a shop's own number (for example on weighed fruit, vegetables or deli items). "
            "Only that shop knows what it means, so no public database has it."])
    if info["is_coupon"]:
        return _result("code", label, "barcode", code, warning=warning,
                       notes=["This is a coupon or refund barcode, not a product."])
    if info["is_issn"]:
        return _result("code", label, "barcode", code, warning=warning,
                       notes=["This is a magazine or newspaper barcode. There's no free database to look it up."])
    if info["is_isbn"]:
        try:
            book = off_client.fetch_book(number)
        except off_client.LookupUnavailable:
            raise ScanError("The book database is not responding. Please try again in a minute.", 503)
        if book:
            return _result("book", book["title"], "open_library", code, item=_book_item(book), warning=warning)
        return _result("code", label, "barcode", code, warning=warning,
                       notes=[f"This book (ISBN {number}) isn't in Open Library yet."])

    food_failed = False
    try:
        product = off_client.fetch_product(number)
    except off_client.LookupUnavailable:
        product, food_failed = None, True
    if product:
        return build_result(product, "open_food_facts", code=code, warning=warning)
    found, other_failed = off_client.fetch_other(number)
    if found:
        key, database, product = found
        return _result("product", product.get("name") or label, f"open_{key}_facts", code,
                       item=_product_item(product, database), warning=warning)
    if food_failed or other_failed:
        raise ScanError("The product databases are not responding. Please try again in a minute.", 503)
    return _result("code", label, "barcode", code, warning=warning, notes=[
        f"This product isn't in {_NOT_FOUND} yet. Anyone can add it for free at openfoodfacts.org."])


def scan_code(text: Any, fmt: Optional[str] = None) -> Dict[str, Any]:
    """Describe any scanned code: product barcode, book, GS1 code, link, payment, Wi-Fi, text..."""
    text = _CONTROL_RE.sub("", str(text if text is not None else "")).strip()
    if not text:
        raise ScanError("Scan a code or type what it says.", 400)
    if len(text) > codes.MAX_CODE_LENGTH:
        raise ScanError("That code is too long to be a barcode or QR code.", 400)
    fmt_name = codes.format_name(fmt)
    code = {"text": text, "format": fmt_name, "facts": [["Scanned as", fmt_name]] if fmt_name else []}

    warning = None
    gtin = None
    gs1 = codes.parse_gs1(text)
    if gs1:
        gtin = gs1["01"]
        extra, warning = codes.describe_gs1(gs1)
        code["facts"] += extra
    elif codes.gs1_digital_link_gtin(text):
        gtin = codes.gs1_digital_link_gtin(text)
        code["facts"].append(["Link", text])
    else:
        compact = re.sub(r"[\s-]", "", text)
        if compact.isdigit() and len(compact) in (8, 12, 13, 14):
            gtin = compact
        elif re.fullmatch(r"\d{9}[\dXx]", compact):
            gtin = codes.isbn10_to_13(compact)

    if gtin:
        info = codes.describe_gtin(gtin, fmt_name)
        if info:
            n = 1 if fmt_name else 0
            code["facts"] = code["facts"][:n] + info["facts"] + code["facts"][n:]
            return _lookup_gtin(info, code, warning)
        if gs1:
            code["facts"].insert(1 if fmt_name else 0, ["Product number", gtin])
            return _result("code", "GS1 product code", "barcode", code, warning=warning,
                           notes=["The product number's check digit doesn't match, so it wasn't looked up."])
        if re.sub(r"[\s-]", "", text).isdigit():
            code["facts"].append(["Number", gtin])
            return _result("code", "Number", "barcode", code, notes=[
                "This isn't a valid product barcode (the last digit doesn't match). "
                "If you typed it, check the digits; if you scanned it, try again."])

    content = codes.describe_content(text)
    notes = [content.pop("note")] if content.get("note") else []
    warning = content.pop("warning", None)
    return _result("code", content["title"], "barcode", code, content=content, warning=warning, notes=notes)


def scan_barcode(barcode: str) -> Dict[str, Any]:
    """Older entry point (typed numbers, the first mobile app)."""
    return scan_code(barcode)


def scan_image(image_bytes: bytes, allow_ai=lambda: True) -> Dict[str, Any]:
    decoded = decode_barcode(image_bytes)
    result = None
    if decoded:
        result = scan_code(*decoded)
        # A product barcode no database knows: with AI on, try reading the label too.
        unknown_product = result["kind"] == "code" and result["code"]["text"].isdigit() and not result.get("content")
        if not (unknown_product and ai_label.enabled()):
            return result
    if not ai_label.enabled():
        raise ScanError("No barcode or QR code found in that photo. Take a sharp, close photo of the code, "
                        "or type it in.", 422)
    if not allow_ai():
        if result:
            return result
        raise ScanError("Label reading is busy today. Please scan or type the barcode instead.", 429)
    label = ai_label.read_label(image_bytes)
    if not label or not (label.get("ingredients_text") or label.get("name")):
        if result:
            return result
        raise ScanError("We couldn't read that label. Try a sharper, well-lit photo of the ingredients list.", 422)
    product = {
        "barcode": off_client.valid_barcode(label.get("barcode")),
        "name": label.get("name"),
        "brand": label.get("brand"),
        "ingredients_text": label.get("ingredients_text"),
    }
    return build_result(product, "label_photo", label_mark=label.get("veg_mark"),
                        declared_allergens=label.get("allergens_declared"))


def verify_image(data: bytes) -> bool:
    """True only for real JPEG/PNG/WebP images."""
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in ("JPEG", "PNG", "WEBP"):
                return False
            img.verify()
        return True
    except Exception:
        return False
