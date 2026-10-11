"""
Food product scanner pipeline.

1. Barcode  -> Open Food Facts (free product database)
2. Photo    -> read a barcode from the photo with OpenCV, then Open Food Facts
3. Photo    -> if GEMINI_API_KEY is set, read the label text with Gemini
Anything we can't identify is reported as "not identified". We never
substitute sample or placeholder products.
"""
import io
import logging
from typing import Any, Dict, Optional

import ai_label
import analysis
import off_client
from nutriscore import calculate_nutri_score_safe

logger = logging.getLogger(__name__)


class ScanError(Exception):
    """A scan that couldn't produce a result. `message` is safe to show users."""

    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.message = message
        self.status = status


def decode_barcode(image_bytes: bytes) -> Optional[str]:
    """Find an EAN/UPC barcode in a photo (zxing-cpp; no system libraries needed)."""
    try:
        import zxingcpp
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img).convert("L")
            img.thumbnail((2000, 2000))
            for result in zxingcpp.read_barcodes(img):
                code = off_client.valid_barcode(result.text)
                if code:
                    return code
    except Exception:
        logger.warning("Barcode decoding failed", exc_info=False)
    return None


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
                 declared_allergens=None) -> Dict[str, Any]:
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
        "source": source,
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


def scan_barcode(barcode: str) -> Dict[str, Any]:
    code = off_client.valid_barcode(barcode)
    if not code:
        raise ScanError("Enter a valid barcode: 8 to 14 digits.", 400)
    try:
        product = off_client.fetch_product(code)
    except off_client.LookupUnavailable:
        raise ScanError("The product database is not responding. Please try again in a minute.", 503)
    if not product:
        raise ScanError(f"Barcode {code} isn't in the Open Food Facts database yet. "
                        "Try a photo of the ingredients label instead.", 404)
    return build_result(product, "open_food_facts")


def scan_image(image_bytes: bytes, allow_ai=lambda: True) -> Dict[str, Any]:
    code = decode_barcode(image_bytes)
    if code:
        try:
            return scan_barcode(code)
        except ScanError as err:
            if err.status not in (404, 503):
                raise
            # fall through to label reading
    if not ai_label.enabled():
        raise ScanError("No barcode found in that photo. Take a sharp, close photo of the barcode, "
                        "or type the barcode number in.", 422)
    if not allow_ai():
        raise ScanError("Label reading is busy today. Please scan or type the barcode instead.", 429)
    label = ai_label.read_label(image_bytes)
    if not label or not (label.get("ingredients_text") or label.get("name")):
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
