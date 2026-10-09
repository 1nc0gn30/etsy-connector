"""Etsy Category Taxonomy Registry & Lookup Engine.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Core Etsy Taxonomy Tree for Print-on-Demand & Digital Assets
ETSY_TAXONOMY_TREE: List[Dict[str, Any]] = [
    {
        "id": 1099,
        "name": "Sweatshirts & Hoodies",
        "path": "Clothing > Gender-Neutral Adult Clothing > Sweaters & Sweatshirts > Sweatshirts",
        "cadre": "apparel",
        "keywords": ["crewneck", "sweatshirt", "pullover", "hoodie", "fleece", "gildan 18000"],
    },
    {
        "id": 1098,
        "name": "T-Shirts",
        "path": "Clothing > Gender-Neutral Adult Clothing > Tops & Tees > T-shirts",
        "cadre": "apparel",
        "keywords": ["tshirt", "tee", "shirt", "graphic tee", "comfort colors 1717"],
    },
    {
        "id": 1085,
        "name": "Mugs",
        "path": "Home & Living > Kitchen & Dining > Drink & Barware > Drinkware > Mugs",
        "cadre": "drinkware",
        "keywords": ["mug", "coffee mug", "tea cup", "ceramic mug", "15oz mug"],
    },
    {
        "id": 1095,
        "name": "Tote Bags",
        "path": "Bags & Purses > Handbags > Totes",
        "cadre": "accessories",
        "keywords": ["tote", "canvas tote", "market bag", "library tote", "grocery bag"],
    },
    {
        "id": 1089,
        "name": "Digital Prints & Wall Art",
        "path": "Art & Collectibles > Prints > Digital Prints",
        "cadre": "digital",
        "keywords": ["wall art", "printable", "digital download", "botanical print", "gallery wall"],
    },
    {
        "id": 1077,
        "name": "Patterns & Blueprints",
        "path": "Craft Supplies & Tools > Patterns & How To > Patterns & Blueprints",
        "cadre": "crafts",
        "keywords": ["pattern", "quilt pattern", "embroidery pattern", "cross stitch", "crochet pattern"],
    },
    {
        "id": 1065,
        "name": "Greeting Cards & Stationery",
        "path": "Paper & Party Supplies > Paper > Greeting Cards",
        "cadre": "stationery",
        "keywords": ["card", "greeting card", "stationery", "postcard", "note card"],
    },
    {
        "id": 1092,
        "name": "Pillows & Cushions",
        "path": "Home & Living > Home Decor > Decorative Pillows",
        "cadre": "home_decor",
        "keywords": ["pillow", "throw pillow", "cushion", "cottagecore pillow"],
    },
]


def get_taxonomy_categories() -> List[Dict[str, Any]]:
    """Return all supported Etsy category taxonomy entries."""
    return ETSY_TAXONOMY_TREE


def find_taxonomy(query: str) -> Optional[Dict[str, Any]]:
    """Search taxonomy by keyword, name, or taxonomy ID."""
    query_str = str(query).lower().strip()
    if query_str.isdigit():
        qid = int(query_str)
        for cat in ETSY_TAXONOMY_TREE:
            if cat["id"] == qid:
                return cat

    for cat in ETSY_TAXONOMY_TREE:
        if query_str in cat["name"].lower() or query_str in cat["path"].lower():
            return cat
        for kw in cat.get("keywords", []):
            if query_str in kw or kw in query_str:
                return cat

    return None
