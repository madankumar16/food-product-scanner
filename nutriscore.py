"""
Nutri-Score Calculator (Python)
Supports basic + category-aware logic (General Foods, Beverages, etc.)
Based on official FSA-NPS / Santé publique France updated algorithm principles.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configures a basic console logging handler for the nutriscore module.
    Useful when importing the module or running it standalone.
    """
    # Remove existing StreamHandlers to avoid duplicate logs if configured multiple times
    for handler in list(logger.handlers):
        if isinstance(handler, logging.StreamHandler):
            logger.removeHandler(handler)
            
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

class NutriScoreCategory(Enum):
    GENERAL_FOODS = "general_foods"
    CHEESE = "cheese"
    RED_MEAT = "red_meat"
    FATS_OILS_NUTS = "fats_oils_nuts"
    BEVERAGE = "beverage"


def map_to_nutriscore_category(
    categories_tags: Optional[List[str]] = None,
    product_name: str = "",
    fallback_to_general: bool = True
) -> NutriScoreCategory:
    """
    Safely maps Open Food Facts categories_tags to Nutri-Score category
    with robust error handling for missing or malformed data.
    """
    try:
        # Handle missing, None, or non-list input
        if categories_tags is None:
            categories_tags = []
        elif not isinstance(categories_tags, list):
            logger.warning(f"Invalid categories_tags type: {type(categories_tags)}. Using fallback.")
            categories_tags = []
        
        # Normalize tags
        tags = {str(t).lower().strip() for t in categories_tags if t}
        
        if not tags and product_name:
            logger.info(f"No categories_tags found for product: {product_name}. Using name-based hints.")
            prod_name_lower = product_name.lower()
            # 1. Beverages
            if any(kw in prod_name_lower for kw in ["water", "juice", "soda", "cola", "milk", "beverage", "drink"]):
                return NutriScoreCategory.BEVERAGE
            # 2. Cheese
            if any(kw in prod_name_lower for kw in ["cheese", "cheddar", "mozzarella", "parmesan", "gouda", "brie"]):
                return NutriScoreCategory.CHEESE
            # 3. Red Meat
            if any(kw in prod_name_lower for kw in ["beef", "pork", "lamb", "goat", "steak", "mutton", "ham", "bacon", "salami"]):
                return NutriScoreCategory.RED_MEAT
            # 4. Fats, Oils, Nuts & Seeds
            if any(kw in prod_name_lower for kw in ["oil", "butter", "margarine", "fat", "nut", "seed", "olive"]):
                return NutriScoreCategory.FATS_OILS_NUTS
        
        # === Priority Checks ===
        
        # 1. Beverages (highest priority for liquid products)
        beverage_keywords = {"en:beverages", "en:plant-based-beverages", "en:milks", 
                           "en:fruit-juices", "en:sodas", "en:water", "en:alcoholic-beverages"}
        if any(kw in tags for kw in beverage_keywords):
            return NutriScoreCategory.BEVERAGE
        
        # 2. Cheese
        if any(kw in tags for kw in {"en:cheeses", "en:cheese", "en:soft-cheeses", "en:hard-cheeses"}):
            return NutriScoreCategory.CHEESE
        
        # 3. Red Meat
        red_meat_keywords = {"en:beef", "en:pork", "en:lamb", "en:goat-meat", 
                           "en:red-meats", "en:processed-meat", "en:charcuterie"}
        if any(kw in tags for kw in red_meat_keywords):
            return NutriScoreCategory.RED_MEAT
        
        # 4. Fats, Oils, Nuts & Seeds
        fat_keywords = {"en:fats", "en:vegetable-oils", "en:olive-oils", "en:butters", 
                       "en:margarines", "en:nuts", "en:seeds", "en:oil-and-fat"}
        if any(kw in tags for kw in fat_keywords) or any("fat" in t or "oil" in t for t in tags):
            return NutriScoreCategory.FATS_OILS_NUTS
        
        # 5. Default
        if not tags and fallback_to_general:
            logger.info(f"No usable category tags found for '{product_name or 'unknown'}'. Defaulting to GENERAL_FOODS.")
        
        return NutriScoreCategory.GENERAL_FOODS

    except Exception as e:
        logger.error(f"Error in category mapping: {e}. Defaulting to GENERAL_FOODS.")
        return NutriScoreCategory.GENERAL_FOODS


def get_energy_points(energy_kj: float) -> int:
    """Negative points for energy (kJ/100g or 100ml)"""
    if energy_kj <= 335: return 0
    elif energy_kj <= 670: return 1
    elif energy_kj <= 1005: return 2
    elif energy_kj <= 1340: return 3
    elif energy_kj <= 1675: return 4
    elif energy_kj <= 2010: return 5
    elif energy_kj <= 2345: return 6
    elif energy_kj <= 2680: return 7
    elif energy_kj <= 3015: return 8
    elif energy_kj <= 3350: return 9
    else: return 10


def get_saturated_fat_points(sat_fat: float) -> int:
    """Negative points for saturated fat (g/100g)"""
    if sat_fat <= 1: return 0
    elif sat_fat <= 2: return 1
    elif sat_fat <= 3: return 2
    elif sat_fat <= 4: return 3
    elif sat_fat <= 5: return 4
    elif sat_fat <= 6: return 5
    elif sat_fat <= 7: return 6
    elif sat_fat <= 8: return 7
    elif sat_fat <= 9: return 8
    elif sat_fat <= 10: return 9
    else: return 10


def get_sugars_points(sugars: float) -> int:
    """Negative points for sugars (g/100g) - updated scale up to 15"""
    if sugars <= 4.5: return 0
    elif sugars <= 9: return 1
    elif sugars <= 13.5: return 2
    elif sugars <= 18: return 3
    elif sugars <= 22.5: return 4
    elif sugars <= 27: return 5
    elif sugars <= 31: return 6
    elif sugars <= 36: return 7
    elif sugars <= 40: return 8
    elif sugars <= 45: return 9
    elif sugars <= 50: return 10
    elif sugars <= 55: return 12
    elif sugars <= 60: return 13
    elif sugars <= 65: return 14
    else: return 15


def get_salt_points(salt: float) -> int:
    """Negative points for salt (g/100g) - updated up to 20"""
    if salt <= 0.3: return 0
    elif salt <= 0.6: return 1
    elif salt <= 0.9: return 2
    elif salt <= 1.2: return 3
    elif salt <= 1.5: return 4
    elif salt <= 1.8: return 5
    elif salt <= 2.1: return 6
    elif salt <= 2.4: return 7
    elif salt <= 2.7: return 8
    elif salt <= 3.0: return 9
    elif salt <= 3.3: return 10
    else: return min(20, int((salt - 0.3) / 0.15) + 1)


def get_fiber_points(fiber: float) -> int:
    """Positive points for fiber (g/100g)"""
    if fiber <= 0.9: return 0
    elif fiber <= 1.9: return 1
    elif fiber <= 2.8: return 2
    elif fiber <= 3.7: return 3
    elif fiber <= 4.7: return 4
    else: return 5


def get_protein_points(protein: float) -> int:
    """Positive points for protein (g/100g)"""
    if protein <= 1.6: return 0
    elif protein <= 3.2: return 1
    elif protein <= 4.8: return 2
    elif protein <= 6.4: return 3
    elif protein <= 8.0: return 4
    elif protein <= 9.6: return 5
    elif protein <= 11.2: return 6
    else: return 7


def get_fruit_veg_points(percentage: float) -> int:
    """Positive points for fruits, vegetables, legumes (%)"""
    if percentage <= 40: return 0
    elif percentage <= 60: return 1
    elif percentage <= 80: return 2
    else: return 5


def calculate_nutri_score(
    energy_kj: float,
    sat_fat: float,
    sugars: float,
    salt: float,
    fiber: float = 0.0,
    protein: float = 0.0,
    fruit_veg_percentage: float = 0.0,
    is_beverage: bool = False,
    is_cheese: bool = False,
    is_fat_oil: bool = False,
    category: Optional[NutriScoreCategory] = None,
    has_non_nutritive_sweeteners: bool = False
) -> dict:
    """
    Main calculation function.
    Returns score, letter, and breakdown.
    """
    # Fallback to map old boolean category flags if category is not provided
    if category is None:
        if is_cheese:
            category = NutriScoreCategory.CHEESE
        elif is_beverage:
            category = NutriScoreCategory.BEVERAGE
        elif is_fat_oil:
            category = NutriScoreCategory.FATS_OILS_NUTS
        else:
            category = NutriScoreCategory.GENERAL_FOODS

    # Negative points (A points)
    neg_energy = get_energy_points(energy_kj)
    neg_sat_fat = get_saturated_fat_points(sat_fat)
    neg_sugars = get_sugars_points(sugars)
    neg_salt = get_salt_points(salt)
    
    negative_points = neg_energy + neg_sat_fat + neg_sugars + neg_salt

    # Positive points (C points)
    pos_fiber = get_fiber_points(fiber)
    pos_protein = get_protein_points(protein)
    
    # Red meat protein capping rule
    if category == NutriScoreCategory.RED_MEAT:
        pos_protein = min(pos_protein, 2)
        
    pos_fvl = get_fruit_veg_points(fruit_veg_percentage)
    
    positive_points = pos_fiber + pos_protein + pos_fvl

    # Special rules
    if negative_points >= 11 and category != NutriScoreCategory.CHEESE:
        positive_points = min(positive_points, pos_fiber + pos_fvl)  # protein may be limited

    final_score = negative_points - positive_points

    # Letter mapping
    if final_score <= -1:
        letter = "A"
    elif final_score <= 2:
        letter = "B"
    elif final_score <= 10:
        letter = "C"
    elif final_score <= 18:
        letter = "D"
    else:
        letter = "E"

    return {
        "final_score": final_score,
        "letter": letter,
        "negative_points": negative_points,
        "positive_points": positive_points,
        "breakdown": {
            "energy": neg_energy,
            "sat_fat": neg_sat_fat,
            "sugars": neg_sugars,
            "salt": neg_salt,
            "fiber": pos_fiber,
            "protein": pos_protein,
            "fruit_veg": pos_fvl
        }
    }


def calculate_nutri_score_safe(
    energy_kj: Optional[float] = 0.0,
    sat_fat: Optional[float] = 0.0,
    sugars: Optional[float] = 0.0,
    salt: Optional[float] = 0.0,
    fiber: Optional[float] = 0.0,
    protein: Optional[float] = 0.0,
    fruit_veg_percentage: Optional[float] = 0.0,
    categories_tags: Optional[List[str]] = None,
    product_name: str = "",
    has_non_nutritive_sweeteners: bool = False
) -> Dict[str, Any]:
    """
    Safe wrapper around calculate_nutri_score with full error handling
    and automatic category detection.
    """
    try:
        # Clean input values (handle None, negative, or missing)
        energy_kj = max(0.0, float(energy_kj or 0))
        sat_fat = max(0.0, float(sat_fat or 0))
        sugars = max(0.0, float(sugars or 0))
        salt = max(0.0, float(salt or 0))
        fiber = max(0.0, float(fiber or 0))
        protein = max(0.0, float(protein or 0))
        fruit_veg_percentage = max(0.0, min(100.0, float(fruit_veg_percentage or 0)))

        # Auto-detect category with error handling
        category = map_to_nutriscore_category(
            categories_tags=categories_tags,
            product_name=product_name
        )

        # Now calculate
        score_data = calculate_nutri_score(
            energy_kj=energy_kj,
            sat_fat=sat_fat,
            sugars=sugars,
            salt=salt,
            fiber=fiber,
            protein=protein,
            fruit_veg_percentage=fruit_veg_percentage,
            category=category,
            has_non_nutritive_sweeteners=has_non_nutritive_sweeteners
        )

        score_data["product_name"] = product_name
        score_data["mapped_category"] = category.value
        return score_data

    except Exception as e:
        logger.error(f"Nutri-Score calculation failed: {e}")
        return {
            "final_score": None,
            "letter": "N/A",
            "error": str(e),
            "negative_points": 0,
            "positive_points": 0,
            "mapped_category": "unknown"
        }


if __name__ == "__main__":
    # Configure logging for direct execution
    configure_logging(logging.DEBUG)
    logger.info("Running standalone Nutri-Score calculation test...")
    test_result = calculate_nutri_score_safe(
        energy_kj=2278,
        sat_fat=11,
        sugars=56.3,
        salt=0.272,
        protein=6.3,
        fiber=3,
        fruit_veg_percentage=13,
        categories_tags=["en:sweet-snacks", "en:biscuits-and-cakes"],
        product_name="Standalone Test Product"
    )
    logger.info(f"Test calculation completed: {test_result['letter']} (Score: {test_result['final_score']})")
