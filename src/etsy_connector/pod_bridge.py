"""Print-on-Demand (POD) Fulfillment Bridge for Etsy (Printify & Gelato).

Maps Etsy product listings to Printify & Gelato fulfillment blueprints and product UIDs.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Standard Printify POD Blueprints
PRINTIFY_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "comfort_colors_1717": {
        "blueprint_id": 638,
        "name": "Comfort Colors 1717 Garment-Dyed T-Shirt",
        "cadre": "apparel",
        "print_provider_id": 29,  # Monster Digital (US Fulfillment)
        "provider_name": "Monster Digital",
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
        "provider_name": "Monster Digital",
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
        "provider_name": "Spoke Custom Products",
        "recommended_retail_usd": 21.99,
        "base_cost_usd": 6.80,
        "canvas_size": {"width": 2400, "height": 1100, "dpi": 300},
        "top_colors": ["Sage Accent", "Dusty Pink Accent", "Classic White"],
    },
    "canvas_tote_heavy": {
        "blueprint_id": 611,
        "name": "Liberty Bags Heavyweight Canvas Tote",
        "cadre": "accessories",
        "print_provider_id": 3,  # SPOKE / US Tote Partner
        "provider_name": "Printify Accessories Partner",
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
        "provider_name": "Direct Etsy Digital Delivery",
        "recommended_retail_usd": 9.99,
        "base_cost_usd": 0.0,
        "canvas_size": {"width": 7200, "height": 10800, "dpi": 300},
        "top_colors": ["Digital ZIP File"],
    },
}

# Standard Gelato POD Catalog (Ecommerce API v4 productUid mapping)
GELATO_PRODUCTS: Dict[str, Dict[str, Any]] = {
    "comfort_colors_1717": {
        "product_uid": "apparel_product_gca_t-shirt_gsc_crewneck_gcu_unisex_gqa_classic_gsi_m_gco_white_gpr_4-0",
        "name": "Gelato Heavyweight Unisex Crewneck T-Shirt",
        "cadre": "apparel",
        "recommended_retail_usd": 32.99,
        "base_cost_usd": 11.95,
        "fulfillment_regions": ["US", "EU", "UK", "AU", "CA"],
        "canvas_size": {"width": 4500, "height": 5400, "dpi": 300},
        "top_colors": ["White", "Sand", "Black", "Forest Green", "Navy"],
    },
    "gildan_18000": {
        "product_uid": "apparel_product_gca_sweatshirt_gsc_crewneck_gcu_unisex_gqa_classic_gsi_m_gco_sand_gpr_4-0",
        "name": "Gelato Heavy Blend Unisex Crewneck Sweatshirt",
        "cadre": "apparel",
        "recommended_retail_usd": 38.99,
        "base_cost_usd": 14.90,
        "fulfillment_regions": ["US", "EU", "UK", "CA"],
        "canvas_size": {"width": 4500, "height": 5400, "dpi": 300},
        "top_colors": ["Sand", "Ash Grey", "Black", "Forest Green"],
    },
    "ceramic_mug_15oz": {
        "product_uid": "mug_product_msz_15-oz_mmat_ceramic-white_cl_4-0",
        "name": "Gelato White Ceramic Mug 15oz",
        "cadre": "drinkware",
        "recommended_retail_usd": 21.99,
        "base_cost_usd": 6.45,
        "fulfillment_regions": ["US", "EU", "UK", "AU"],
        "canvas_size": {"width": 2400, "height": 1100, "dpi": 300},
        "top_colors": ["Glossy White"],
    },
    "canvas_tote_heavy": {
        "product_uid": "bag_product_bt_tote-bag_bmat_cotton-heavy_bco_natural_gpr_4-0",
        "name": "Gelato Heavyweight Cotton Tote Bag",
        "cadre": "accessories",
        "recommended_retail_usd": 24.99,
        "base_cost_usd": 7.10,
        "fulfillment_regions": ["US", "EU", "UK"],
        "canvas_size": {"width": 3600, "height": 3600, "dpi": 300},
        "top_colors": ["Natural", "Black"],
    },
    "fine_art_poster_18x24": {
        "product_uid": "flat_18x24-inch-45x60-cm_200-gsm-uncoated-matte_4-0_ver",
        "name": "Gelato Archival Matte Fine Art Poster (18×24 in / 200gsm)",
        "cadre": "wall_art",
        "recommended_retail_usd": 29.99,
        "base_cost_usd": 9.40,
        "fulfillment_regions": ["US", "EU", "UK", "AU", "JP", "CA"],
        "canvas_size": {"width": 5400, "height": 7200, "dpi": 300},
        "top_colors": ["Museum Matte 200gsm"],
    },
    "digital_wall_art_pack": {
        "product_uid": "digital_direct_etsy_zip_300dpi",
        "name": "Instant Digital Download Wall Art Pack (300 DPI 5-Ratio ZIP)",
        "cadre": "digital",
        "recommended_retail_usd": 9.99,
        "base_cost_usd": 0.0,
        "fulfillment_regions": ["GLOBAL_DIGITAL"],
        "canvas_size": {"width": 7200, "height": 10800, "dpi": 300},
        "top_colors": ["Digital ZIP File"],
    },
}


def get_available_blueprints(provider: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Return supported Print-on-Demand product blueprints (Printify or Gelato)."""
    prov = (provider or "printify").strip().lower()
    if prov == "gelato":
        return GELATO_PRODUCTS
    return PRINTIFY_BLUEPRINTS


def get_all_provider_catalogs() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Return both Printify and Gelato catalogs."""
    return {
        "printify": PRINTIFY_BLUEPRINTS,
        "gelato": GELATO_PRODUCTS,
    }


def generate_printify_product_payload(
    blueprint_key: str,
    title: str,
    description: str,
    tags: List[str],
    design_image_url: str,
    retail_price_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate Printify REST API JSON payload for product creation and Etsy sync."""
    key = blueprint_key if blueprint_key in PRINTIFY_BLUEPRINTS else "comfort_colors_1717"
    bp = PRINTIFY_BLUEPRINTS[key]
    price = round(float(retail_price_usd if retail_price_usd is not None else bp["recommended_retail_usd"]), 2)
    price_cents = int(round(price * 100))

    return {
        "provider": "printify",
        "blueprint_key": key,
        "title": title,
        "description": description,
        "blueprint_id": bp["blueprint_id"],
        "print_provider_id": bp["print_provider_id"],
        "tags": list(tags or [])[:13],
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
            "provider": "printify",
            "provider_name": bp["provider_name"],
            "cadre": bp["cadre"],
            "base_cost_usd": bp["base_cost_usd"],
            "retail_price_usd": price,
            "canvas_specs": bp["canvas_size"],
        },
    }


def generate_gelato_product_payload(
    blueprint_key: str,
    title: str,
    description: str,
    tags: List[str],
    design_image_url: str,
    retail_price_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate Gelato Ecommerce API v4 product creation payload for localized Etsy fulfillment."""
    key = blueprint_key if blueprint_key in GELATO_PRODUCTS else "comfort_colors_1717"
    gp = GELATO_PRODUCTS[key]
    price = round(float(retail_price_usd if retail_price_usd is not None else gp["recommended_retail_usd"]), 2)

    return {
        "provider": "gelato",
        "blueprint_key": key,
        "apiVersion": "v4",
        "endpoint": "POST https://ecommerce.gelatoapis.com/v1/stores/{storeId}/products:create-from-template",
        "title": title,
        "description": description,
        "tags": list(tags or [])[:13],
        "isVisibleInTheOnlineStore": False,
        "salesChannels": ["etsy"],
        "variants": [
            {
                "productUid": gp["product_uid"],
                "retailPrice": {"amount": price, "currency": "USD"},
                "imagePlaceholders": [
                    {
                        "name": "front",
                        "fileUrl": design_image_url,
                        "fitMethod": "meet",
                    }
                ],
            }
        ],
        "metadata": {
            "source": "etsy-connector",
            "provider": "gelato",
            "cadre": gp["cadre"],
            "base_cost_usd": gp["base_cost_usd"],
            "retail_price_usd": price,
            "fulfillment_regions": gp["fulfillment_regions"],
            "canvas_specs": gp["canvas_size"],
        },
    }


def generate_pod_payload(
    blueprint_key: str,
    title: str,
    description: str,
    tags: List[str],
    design_image_url: str,
    retail_price_usd: Optional[float] = None,
    provider: str = "printify",
) -> Dict[str, Any]:
    """Generate Printify or Gelato POD fulfillment payload."""
    prov = (provider or "printify").strip().lower()
    if prov == "gelato":
        return generate_gelato_product_payload(
            blueprint_key=blueprint_key,
            title=title,
            description=description,
            tags=tags,
            design_image_url=design_image_url,
            retail_price_usd=retail_price_usd,
        )
    if prov != "printify":
        raise ValueError(f"Unsupported POD provider '{provider}'. Supported: 'printify', 'gelato'.")
    return generate_printify_product_payload(
        blueprint_key=blueprint_key,
        title=title,
        description=description,
        tags=tags,
        design_image_url=design_image_url,
        retail_price_usd=retail_price_usd,
    )
