"""
Nutri-Score calculator following the 2023 updated algorithm published by
Santé publique France (foods, cheese, red meat, fats/oils/nuts/seeds and
beverages). Values are per 100 g (or 100 ml for drinks).

Every threshold table below is "lower bounds": a value strictly greater than
the n-th bound earns n points.
"""
import logging
import re
from bisect import bisect_left
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class NutriScoreCategory(Enum):
    GENERAL_FOODS = "general_foods"
    CHEESE = "cheese"
    RED_MEAT = "red_meat"
    FATS_OILS_NUTS = "fats_oils_nuts"
    BEVERAGE = "beverage"


def _points(value: float, bounds: List[float], values: Optional[List[int]] = None) -> int:
    """Points = number of bounds the value strictly exceeds (or mapped value)."""
    idx = bisect_left(bounds, value)  # count of bounds < value
    if values is not None:
        return values[idx]
    return idx

# ---------------- Foods (also cheese and red meat) ----------------
FOOD_ENERGY = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]          # 0–10
FOOD_SUGARS = [3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51]       # 0–15
SAT_FAT = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]                                          # 0–10
SALT = [0.2 * i for i in range(1, 21)]                                             # 0–20
FOOD_PROTEIN = [2.4, 4.8, 7.2, 9.6, 12, 14, 17]                                    # 0–7
FIBRE = [3.0, 4.1, 5.2, 6.3, 7.4]                                                  # 0–5
FOOD_FVL_BOUNDS, FOOD_FVL_VALUES = [40, 60, 80], [0, 1, 2, 5]

# ---------------- Fats, oils, nuts and seeds ----------------
SAT_ENERGY = [120 * i for i in range(1, 11)]                                       # kJ from sat. fat, 0–10
SAT_RATIO = [10, 16, 22, 28, 34, 40, 46, 52, 58, 64]                               # % sat/total fat, 0–10

# ---------------- Beverages ----------------
BEV_ENERGY = [30, 90, 150, 210, 240, 270, 300, 330, 360, 390]                      # 0–10
BEV_SUGARS = [0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11]                                  # 0–10
BEV_PROTEIN = [1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0]                                  # 0–7
BEV_FVL_BOUNDS, BEV_FVL_VALUES = [40, 60, 80], [0, 2, 4, 6]


def _ratio_points(sat_fat: float, fat: float) -> int:
    if fat <= 0:
        return 0
    ratio = 100.0 * sat_fat / fat
    # "< 10 → 0, < 16 → 1 ..." — a ratio exactly on a bound moves up a band
    return sum(1 for b in SAT_RATIO if ratio >= b)


def _letter(score: int, category: NutriScoreCategory, is_water: bool) -> str:
    if category == NutriScoreCategory.BEVERAGE:
        if is_water:
            return "A"
        if score <= 2:
            return "B"
        if score <= 6:
            return "C"
        if score <= 9:
            return "D"
        return "E"
    if category == NutriScoreCategory.FATS_OILS_NUTS:
        if score <= -6:
            return "A"
        if score <= 2:
            return "B"
    else:
        if score <= 0:
            return "A"
        if score <= 2:
            return "B"
    if score <= 10:
        return "C"
    if score <= 18:
        return "D"
    return "E"


def calculate_nutri_score(
    energy_kj: float,
    sat_fat: float,
    sugars: float,
    salt: float,
    fiber: float = 0.0,
    protein: float = 0.0,
    fruit_veg_percentage: float = 0.0,
    category: Optional[NutriScoreCategory] = None,
    fat: Optional[float] = None,
    has_non_nutritive_sweeteners: bool = False,
    is_water: bool = False,
) -> Dict[str, Any]:
    """Return the score, letter and per-component points."""
    category = category or NutriScoreCategory.GENERAL_FOODS
    breakdown: Dict[str, int] = {}

    if category == NutriScoreCategory.BEVERAGE:
        breakdown["energy"] = _points(energy_kj, BEV_ENERGY)
        breakdown["sugars"] = _points(sugars, BEV_SUGARS)
        breakdown["sat_fat"] = _points(sat_fat, SAT_FAT)
        breakdown["salt"] = _points(salt, SALT)
        breakdown["sweeteners"] = 4 if has_non_nutritive_sweeteners else 0
        breakdown["protein"] = _points(protein, BEV_PROTEIN)
        breakdown["fiber"] = _points(fiber, FIBRE)
        breakdown["fruit_veg"] = _points(fruit_veg_percentage, BEV_FVL_BOUNDS, BEV_FVL_VALUES)
        negative = breakdown["energy"] + breakdown["sugars"] + breakdown["sat_fat"] + breakdown["salt"] + breakdown["sweeteners"]
        positive = breakdown["protein"] + breakdown["fiber"] + breakdown["fruit_veg"]
    else:
        if category == NutriScoreCategory.FATS_OILS_NUTS:
            breakdown["energy"] = _points(sat_fat * 37.0, SAT_ENERGY)       # energy from saturates
            breakdown["sat_fat"] = _ratio_points(sat_fat, fat if fat is not None else 0.0)
        else:
            breakdown["energy"] = _points(energy_kj, FOOD_ENERGY)
            breakdown["sat_fat"] = _points(sat_fat, SAT_FAT)
        breakdown["sugars"] = _points(sugars, FOOD_SUGARS)
        breakdown["salt"] = _points(salt, SALT)
        breakdown["protein"] = _points(protein, FOOD_PROTEIN)
        if category == NutriScoreCategory.RED_MEAT:
            breakdown["protein"] = min(breakdown["protein"], 2)
        breakdown["fiber"] = _points(fiber, FIBRE)
        breakdown["fruit_veg"] = _points(fruit_veg_percentage, FOOD_FVL_BOUNDS, FOOD_FVL_VALUES)
        negative = breakdown["energy"] + breakdown["sat_fat"] + breakdown["sugars"] + breakdown["salt"]
        protein_limit = 7 if category == NutriScoreCategory.FATS_OILS_NUTS else 11
        if category != NutriScoreCategory.CHEESE and negative >= protein_limit:
            positive = breakdown["fiber"] + breakdown["fruit_veg"]       # protein not counted
            breakdown["protein_counted"] = 0
        else:
            positive = breakdown["protein"] + breakdown["fiber"] + breakdown["fruit_veg"]
            breakdown["protein_counted"] = 1

    score = negative - positive
    return {
        "final_score": score,
        "letter": _letter(score, category, is_water),
        "negative_points": negative,
        "positive_points": positive,
        "category": category.value,
        "breakdown": breakdown,
    }


_NAME_HINTS = [
    (NutriScoreCategory.BEVERAGE, r"\b(water|juice|soda|cola|drink|beverage|lassi|buttermilk|milk|tea|coffee)\b"),
    (NutriScoreCategory.CHEESE, r"\b(cheese|cheddar|mozzarella|parmesan|gouda|brie|paneer)\b"),
    (NutriScoreCategory.RED_MEAT, r"\b(beef|pork|lamb|mutton|goat|steak|ham|bacon|salami)\b"),
    (NutriScoreCategory.FATS_OILS_NUTS, r"\b(oil|ghee|butter|margarine|almonds?|cashews?|walnuts?|peanuts?|seeds?)\b"),
]
_TAGS = {
    NutriScoreCategory.BEVERAGE: {"en:beverages", "en:plant-based-beverages", "en:milks", "en:fruit-juices",
                                  "en:sodas", "en:waters", "en:teas", "en:coffees"},
    NutriScoreCategory.CHEESE: {"en:cheeses"},
    NutriScoreCategory.RED_MEAT: {"en:beef", "en:pork", "en:lamb-meat", "en:goat-meat", "en:red-meats"},
    NutriScoreCategory.FATS_OILS_NUTS: {"en:fats", "en:vegetable-oils", "en:olive-oils", "en:butters",
                                        "en:margarines", "en:nuts", "en:seeds", "en:ghee"},
}


def map_to_nutriscore_category(categories_tags: Optional[List[str]] = None,
                               product_name: str = "") -> NutriScoreCategory:
    tags = {str(t).lower().strip() for t in (categories_tags or []) if t}
    for category in (NutriScoreCategory.BEVERAGE, NutriScoreCategory.CHEESE,
                     NutriScoreCategory.RED_MEAT, NutriScoreCategory.FATS_OILS_NUTS):
        if tags & _TAGS[category]:
            return category
    if not tags and product_name:
        name = product_name.lower()
        for category, pattern in _NAME_HINTS:
            if re.search(pattern, name):
                return category
    return NutriScoreCategory.GENERAL_FOODS


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
    fat: Optional[float] = None,
    has_non_nutritive_sweeteners: bool = False,
) -> Dict[str, Any]:
    """Clean the inputs, detect the category and calculate. Never raises."""
    def clean(v, hi=None):
        try:
            v = max(0.0, float(v or 0))
        except (TypeError, ValueError):
            v = 0.0
        return min(v, hi) if hi is not None else v
    try:
        category = map_to_nutriscore_category(categories_tags, product_name)
        result = calculate_nutri_score(
            energy_kj=clean(energy_kj), sat_fat=clean(sat_fat), sugars=clean(sugars), salt=clean(salt),
            fiber=clean(fiber), protein=clean(protein), fruit_veg_percentage=clean(fruit_veg_percentage, 100),
            category=category, fat=clean(fat) if fat is not None else None,
            has_non_nutritive_sweeteners=has_non_nutritive_sweeteners,
            is_water="en:waters" in {str(t).lower() for t in (categories_tags or [])},
        )
        result["mapped_category"] = category.value
        return result
    except Exception:  # pragma: no cover - defensive
        logger.exception("Nutri-Score calculation failed")
        return {"final_score": None, "letter": None, "mapped_category": "unknown"}
