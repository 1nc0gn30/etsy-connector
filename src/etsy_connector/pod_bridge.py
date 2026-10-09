"""Print-on-Demand (POD) Fulfillment Bridge for Etsy.

Maps Etsy product listings to Printify & Gelato fulfillment blueprints.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Standard Printify POD Blueprints for Day 7 Winning Cadres
PRINTIFY_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "comfort_colors_1717": {
        "blueprint_id": 638,
        "name": "Comfort Colors 1717 Garment-Dyed T-Shirt",
        "cadre": "apparel",
        "print_provider_id": 29,  # Monster Digital (Top US Fulfillment)
        "recommended_retail_usd": 32.99,
        "base_cost_usd": 12.80,
        "canvas_size": {"width": 4500, "height": 5400, "dpi": 300},
        "top_colors": ["Sand", "Pepper", "Moss", "Terracotta", "Ivory", "Dusty Rose"],
    },
    "gildan_18000": {
        "blueprint_id": 49,
        "name": "Gildan 18000 Heavy Blend Crewneck Sweatshirt",
        "cadre": "apparel",
        "print_provider_id": 29,  # Monster Digital
        "recommended_retail_usd": 38.99,
        "base_cost_usd": 15.50,
        "canvas_size": {"width": 4500, "height": 5400, "dpi": 300},
        "top_colors": ["Sand", "Forest Green", "Ash Grey", "Light Pink", "Maroon"],
    },
    "ceramic_mug_15oz": {
        "blueprint_id": 68,
        "name": "Ceramic Accent Mug 15oz",
        "cadre": "drinkware",
        "print_provider_id": 26,  # Spoke Custom Products
        "recommended_retail_usd": 21.99,
        "base_cost_usd": 6.80,
        "canvas_size": {"width": 2400, "height": 1100, "dpi": 300},
        "top_colors": ["Sage Accent", "Dusty Pink Accent", "Classic White"],
    },
    "canvas_tote_heavy": {
        "blueprint_id": 611,
        "name": "Liberty Bags Heavyweight Canvas Tote",
        "cadre": "accessories",
        "print_provider_id": 3,
        "recommended_retail_usd": 24.99,
        "base_cost_usd": 7.20,
        "canvas_size": {"width": 3600, "height": 3600, "dpi": 300},
        "top_colors": ["Natural Canvas", "Black", "Forest Green"],
    },
    "digital_wall_art_pack": {
        "blueprint_id": 0,  # Zero fulfillment overhead (Instant Digital Download)
        "name": "Instant Digital Download Wall Art Pack (300 DPI 5-Ratio ZIP)",
        "cadre": "digital",
        "print_provider_id": 0,
        "recommended_retail_usd": 9.99,
        "base_cost_usd": 0.0,
        "canvas_size": {"width": 7200, "height": 10800, "dpi": 300},
        "top_colors": ["Digital ZIP File"],
    },
}


def get_available_blueprints() -> Dict[str, Dict[str, Any]]:
    """Return all supported Print-on-Demand product blueprints."""
    return PRINTIFY_BLUEPRINTS


def generate_printify_product_payload(
    blueprint_key: str,
    title: str,
    description: str,
    tags: List[str],
    design_image_url: str,
    retail_price_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate Printify REST API JSON payload for automated product creation and Etsy sync."""
    bp = PRINTIFY_BLUEPRINTS.get(blueprint_key, PRINTIFY_BLUEPRINTS["comfort_colors_1717"])
    price = retail_price_usd or bp["recommended_retail_usd"]
    price_cents = int(price * 100)

    payload = {
        "title": title,
        "description": description,
        "blueprint_id": bp["blueprint_id"],
        "print_provider_id": bp["print_provider_id"],
        "tags": tags[:13],
        "variants": [
            {
                "id": 1,
                "price": price_cents,
                "is_enabled": True,
            }
        ],
        "print_areas": [
            {
                "position": "front",
                "images": [
                    {
                        "id": "img_primary_design",
                        "src": design_image_url,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0,
                    }
                ],
            }
        ],
        "metadata": {
            "source": "etsy-connector",
            "cadre": bp["cadre"],
            "canvas_specs": bp["canvas_size"],
            "target_demographic": "55+ Women Gifts & Cottagecore",
        },
    }
    return payload
