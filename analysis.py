"""
Rule-based ingredient analysis: splitting an ingredients list, vegetarian
status, allergen flags and a simple ingredient score.

Nothing here is made up: if we don't have ingredients we say so, and the
vegetarian status is only "Vegetarian" when a reliable source confirms it.
"""
import re
from typing import Dict, Iterable, List, Optional

VEG = "Vegetarian"
VEGAN = "Vegan"
NON_VEG = "Non-Vegetarian"
UNKNOWN = "Not confirmed"

# Indian convention: eggs count as non-vegetarian.
_NON_VEG_TERMS = [
    "chicken", "mutton", "lamb", "beef", "pork", "ham", "bacon", "veal", "goat meat", "meat",
    "fish", "tuna", "salmon", "sardine", "anchov", "prawn", "shrimp", "crab", "lobster", "squid",
    "oyster", "mussel", "shellfish", "egg", "albumen", "gelatin", "gelatine", "lard", "tallow",
    "suet", "collagen", "isinglass", "rennet", "carmine", "cochineal", "e120", "e441", "e542",
    "e904", "shellac", "chondroitin", "fish oil", "fish sauce", "oyster sauce", "bone",
]
_ANIMAL_BUT_VEG_TERMS = ["milk", "butter", "ghee", "cream", "cheese", "paneer", "curd", "yogurt",
                         "yoghurt", "whey", "casein", "lactose", "honey", "beeswax", "e901"]
# Words that contain a non-veg term but are not non-veg.
_FALSE_FRIENDS = ["eggplant", "egg-free", "eggless", "egg free", "butterfly", "peanut butter",
                  "cocoa butter", "shea butter", "coconut milk", "almond milk", "oat milk",
                  "soy milk", "soya milk", "rice milk", "fish-free", "meatless", "meat-free",
                  "vegetable gelatin", "agar", "coconut meat"]

_ALLERGENS: Dict[str, List[str]] = {
    "Milk": ["milk", "butter", "ghee", "cream", "cheese", "paneer", "curd", "yogurt", "yoghurt", "whey", "casein", "lactose"],
    "Egg": ["egg", "albumen"],
    "Peanut": ["peanut", "groundnut"],
    "Tree nuts": ["almond", "cashew", "walnut", "hazelnut", "pistachio", "pecan", "macadamia", "brazil nut"],
    "Gluten (wheat, barley, rye)": ["wheat", "maida", "atta", "semolina", "suji", "barley", "rye", "malt", "gluten", "spelt"],
    "Soy": ["soy", "soya"],
    "Sesame": ["sesame", "til "],
    "Mustard": ["mustard"],
    "Fish": ["fish", "tuna", "salmon", "sardine", "anchov"],
    "Crustaceans / shellfish": ["prawn", "shrimp", "crab", "lobster", "shellfish", "oyster", "mussel"],
    "Sulphites": ["sulphite", "sulfite", "e220", "e221", "e222", "e223", "e224", "e228"],
}

# Ingredients worth limiting. Weights feed the simple ingredient score.
_CONCERNS = [
    (r"\b(sugar|glucose|fructose|sucrose|dextrose|corn syrup|invert syrup|jaggery)\b", "Added sugar", 6),
    (r"\b(hydrogenated|partially hydrogenated|vanaspati|shortening)\b", "Hydrogenated fat (may contain trans fat)", 15),
    (r"\b(palm oil|palmolein|palm fat)\b", "Palm oil (high in saturated fat)", 5),
    (r"\b(salt|sodium chloride)\b", "Added salt", 3),
    (r"\b(msg|monosodium glutamate|e621)\b", "Flavour enhancer (MSG)", 4),
    (r"\b(aspartame|acesulfame|sucralose|saccharin|e95[0-5])\b", "Artificial sweetener", 5),
    (r"\b(e10[0-9]|e1[1-6][0-9]|tartrazine|sunset yellow|allura red|carmoisine|ponceau)\b", "Added colour", 4),
    (r"\b(e2[0-9][0-9]|sodium benzoate|potassium sorbate|nitrite|nitrate)\b", "Preservative", 4),
    (r"\b(artificial flavou?r|synthetic flavou?r)\b", "Artificial flavouring", 3),
    (r"\b(caffeine)\b", "Caffeine", 3),
]


def split_ingredients(text: Optional[str]) -> List[str]:
    """Split an ingredients text into a clean list (keeps text in brackets with its ingredient)."""
    if not text:
        return []
    text = re.sub(r"^\s*ingredients?\s*[:\-]\s*", "", text.strip(), flags=re.I)
    parts, depth, current = [], 0, []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch in ",;" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    cleaned = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip(" .*_-\t\n")
        if p and len(p) <= 200 and p.lower() not in (c.lower() for c in cleaned):
            cleaned.append(p)
    return cleaned[:150]


def _contains(text: str, term: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(term), text) is not None


def _strip_false_friends(text: str) -> str:
    for ff in _FALSE_FRIENDS:
        text = text.replace(ff, " ")
    return text


def veg_status(ingredients: Iterable[str], source_tags: Optional[Iterable[str]] = None,
               label_mark: Optional[str] = None) -> Dict[str, str]:
    """
    Decide vegetarian status. Order of trust:
    1. Non-veg ingredients found in the list  -> Non-Vegetarian
    2. FSSAI mark read from the label (brown = non-veg, green = veg)
    3. Open Food Facts analysis tags
    4. Otherwise "Not confirmed"
    """
    text = _strip_false_friends(" " + " ".join(i.lower() for i in ingredients) + " ")
    hits = sorted({t for t in _NON_VEG_TERMS if _contains(text, t)})
    if hits:
        return {"status": NON_VEG, "reason": "Contains " + ", ".join(hits[:5])}
    if label_mark == "brown":
        return {"status": NON_VEG, "reason": "Brown non-veg mark on the label"}
    tags = {t.lower() for t in (source_tags or [])}
    if "en:non-vegetarian" in tags:
        return {"status": NON_VEG, "reason": "Open Food Facts lists it as non-vegetarian"}
    if label_mark == "green":
        return {"status": VEG, "reason": "Green veg mark on the label"}
    if "en:vegan" in tags:
        return {"status": VEGAN, "reason": "Open Food Facts lists it as vegan"}
    if "en:vegetarian" in tags:
        return {"status": VEG, "reason": "Open Food Facts lists it as vegetarian"}
    return {"status": UNKNOWN, "reason": "Check for the green or brown dot on the pack"}


def allergens(ingredients: Iterable[str], declared: Optional[Iterable[str]] = None) -> List[str]:
    text = _strip_false_friends(" " + " ".join(i.lower() for i in ingredients) + " ")
    # plant "milks" and nut butters still contain their nut/soy allergen
    raw = " " + " ".join(i.lower() for i in ingredients) + " "
    found = []
    for name, terms in _ALLERGENS.items():
        source = text if name in ("Milk", "Egg", "Fish") else raw
        if any(_contains(source, t) for t in terms):
            found.append(name)
    for d in declared or []:
        d = str(d).replace("en:", "").replace("-", " ").strip().capitalize()
        if d and not any(d.lower() in f.lower() for f in found):
            found.append(d)
    return found


def ingredient_score(ingredients: List[str]) -> Dict[str, object]:
    """
    A simple 0–100 rule-based score (100 = nothing flagged). It is a rough
    guide to processed ingredients, not a food-safety rating.
    """
    if not ingredients:
        return {"score": None, "band": "UNKNOWN", "flags": []}
    text = " " + " ".join(i.lower() for i in ingredients) + " "
    flags, score = [], 100
    for pattern, label, weight in _CONCERNS:
        if re.search(pattern, text):
            flags.append(label)
            score -= weight
    score = max(0, score)
    band = "GREEN" if score >= 85 else "YELLOW" if score >= 70 else "RED"
    return {"score": score, "band": band, "flags": flags}
