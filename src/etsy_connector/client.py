"""Etsy Open API v3 Client with Resilient Simulation Mode.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .taxonomy import find_taxonomy, get_taxonomy_categories

CONFIG_PATH = Path.home() / ".etsy_connector_config.json"


class EtsyClient:
    """Etsy Open API v3 HTTP client with transparent simulation mode."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        shop_id: Optional[str] = None,
        simulate: Optional[bool] = None,
    ) -> None:
        # Load from arguments, env vars, or local config
        config = self._load_config()
        self.api_key = api_key or os.environ.get("ETSY_API_KEY") or config.get("api_key", "")
        self.access_token = access_token or os.environ.get("ETSY_ACCESS_TOKEN") or config.get("access_token", "")
        self.shop_id = shop_id or os.environ.get("ETSY_SHOP_ID") or config.get("shop_id", "")

        # If simulate not explicitly given, simulate if credentials are missing
        if simulate is not None:
            self.simulate = simulate
        else:
            self.simulate = not (self.api_key and self.access_token)

        self.base_url = "https://openapi.etsy.com/v3/application"

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_PATH.exists():
            try:
                return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def save_credentials(self, api_key: str, access_token: str, shop_id: str) -> None:
        """Persist API credentials to user config file."""
        self.api_key = api_key.strip()
        self.access_token = access_token.strip()
        self.shop_id = shop_id.strip()
        self.simulate = not (self.api_key and self.access_token)
        CONFIG_PATH.write_text(
            json.dumps(
                {
                    "api_key": self.api_key,
                    "access_token": self.access_token,
                    "shop_id": self.shop_id,
                    "updated_at": time.time(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def is_configured(self) -> bool:
        """Return True if live credentials are configured."""
        return bool(self.api_key and self.access_token)

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute HTTP request against Etsy API v3 or fallback to simulation."""
        if self.simulate:
            return self._simulate_response(endpoint, method, params, payload)

        url = f"{self.base_url}{endpoint}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"

        data = json.dumps(payload).encode("utf-8") if payload else None
        headers = {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "AntigravityEtsyConnector/0.1.0",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            # Fallback to simulation if auth failed
            if e.code in (401, 403):
                return self._simulate_response(endpoint, method, params, payload, note=f"Live API error ({e.code}); fell back to simulation.")
            raise RuntimeError(f"Etsy API HTTP {e.code}: {err_body}")
        except Exception as e:
            return self._simulate_response(endpoint, method, params, payload, note=f"Network error ({e}); fell back to simulation.")

    def _simulate_response(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate high-fidelity simulated response for testing and offline development."""
        sim_id = f"etsy_sim_{uuid.uuid4().hex[:8]}"

        if "/shops/" in endpoint and endpoint.endswith("/listings"):
            # Create listing simulation
            p = payload or {}
            return {
                "simulation": True,
                "status": "draft",
                "listing_id": 1827495000 + int(time.time() % 100000),
                "title": p.get("title", "Simulated Etsy Listing"),
                "description": p.get("description", ""),
                "state": "draft",
                "price": {"amount": int((p.get("price", 34.99) or 34.99) * 100), "divisor": 100, "currency_code": "USD"},
                "quantity": p.get("quantity", 999),
                "tags": p.get("tags", []),
                "taxonomy_id": p.get("taxonomy_id", 1099),
                "url": f"https://www.etsy.com/listing/simulated/{sim_id}",
                "created_timestamp": int(time.time()),
                "note": note or "Simulated Etsy draft listing created (Live API Key not active).",
            }

        if "/listings/active" in endpoint:
            # Search active listings simulation
            kw = (params or {}).get("keywords", "wildflower sweatshirt")
            mock_results = [
                {
                    "listing_id": 1782349011,
                    "title": f"Grandma's Garden Wildflower Sweatshirt, Cozy Cottagecore Gift, Floral Embroidered Print Crewneck",
                    "price": {"amount": 3699, "divisor": 100, "currency_code": "USD"},
                    "tags": ["grandma sweatshirt", "garden crewneck", "cottagecore gift", "wildflower shirt", "mothers day gift", "comfort colors 1717", "plant lover gift"],
                    "views": 4820,
                    "num_favorers": 1240,
                    "shop_name": "BotanicalHavenPrints",
                    "rating": 4.95,
                },
                {
                    "listing_id": 1782349012,
                    "title": f"Vintage Songbird Watercolor Ceramic Coffee Mug 15oz, Backyard Birdwatcher Tea Cup, Country Kitchen Decor",
                    "price": {"amount": 2199, "divisor": 100, "currency_code": "USD"},
                    "tags": ["songbird mug", "birdwatcher gift", "watercolor tea cup", "chickadee ceramic", "grandma coffee cup", "cottagecore mug"],
                    "views": 2910,
                    "num_favorers": 820,
                    "shop_name": "MorningMeadowStudio",
                    "rating": 4.98,
                },
                {
                    "listing_id": 1782349013,
                    "title": f"Heavyweight Canvas Farmers Market Tote Bag, French Lavender & Herb Botanical Grocery Bag, Library Book Tote",
                    "price": {"amount": 2499, "divisor": 100, "currency_code": "USD"},
                    "tags": ["canvas tote bag", "farmers market", "lavender tote", "french botanical", "library tote", "cottagecore bag"],
                    "views": 1840,
                    "num_favorers": 490,
                    "shop_name": "HeirloomLivingCo",
                    "rating": 4.92,
                },
            ]
            return {
                "simulation": True,
                "count": len(mock_results),
                "results": mock_results,
                "keywords": kw,
                "note": note or "Simulated Etsy search results for competitor & niche keyword intelligence.",
            }

        if "/shops/" in endpoint:
            # Shop info simulation
            return {
                "simulation": True,
                "shop_id": self.shop_id or "99882211",
                "shop_name": "GrandmasGardenPrints",
                "title": "Cozy Botanical Apparel, Songbird Mugs & Nostalgic Gifts",
                "currency_code": "USD",
                "listing_active_count": 28,
                "digital_listing_count": 12,
                "review_count": 348,
                "review_average": 4.96,
                "is_vacation": False,
                "note": note or "Simulated Etsy shop profile.",
            }

        return {
            "simulation": True,
            "status": "success",
            "endpoint": endpoint,
            "timestamp": time.time(),
            "note": note or "Simulated generic Etsy response.",
        }

    def get_shop(self, shop_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch shop details from Etsy Open API v3."""
        target_shop = shop_id or self.shop_id or "me"
        return self._request(f"/shops/{target_shop}")

    def search_listings(
        self,
        keywords: str,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Search active Etsy listings for competitor analysis, keywords, and prices."""
        params: Dict[str, Any] = {"keywords": keywords, "limit": max(1, min(limit, 100))}
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        return self._request("/listings/active", params=params)

    def create_draft_listing(
        self,
        title: str,
        description: str,
        price: float,
        quantity: int = 999,
        tags: Optional[List[str]] = None,
        taxonomy_id: int = 1099,
        who_made: str = "collective",
        when_made: str = "2020_2026",
        is_supply: bool = False,
    ) -> Dict[str, Any]:
        """Create a draft listing on Etsy."""
        target_shop = self.shop_id or "me"
        payload = {
            "quantity": quantity,
            "title": title[:140],
            "description": description,
            "price": price,
            "who_made": who_made,
            "when_made": when_made,
            "taxonomy_id": taxonomy_id,
            "is_supply": is_supply,
            "tags": (tags or [])[:13],
            "state": "draft",
        }
        return self._request(f"/shops/{target_shop}/listings", method="POST", payload=payload)

    def upload_listing_image(
        self,
        listing_id: str,
        image_path: str,
        rank: int = 1,
    ) -> Dict[str, Any]:
        """Upload product mockup or design image to Etsy listing."""
        if self.simulate or not self.is_configured():
            return {
                "simulation": True,
                "status": "uploaded",
                "listing_id": listing_id,
                "image_id": f"img_{uuid.uuid4().hex[:8]}",
                "rank": rank,
                "url_570xN": f"https://i.etsystatic.com/simulated/{listing_id}_570xN.jpg",
                "url_fullxfull": f"https://i.etsystatic.com/simulated/{listing_id}_fullxfull.jpg",
            }

        # Live multipart upload
        target_shop = self.shop_id or "me"
        endpoint = f"/shops/{target_shop}/listings/{listing_id}/images"
        # Return structured instruction or handle live multipart
        return {"status": "ready", "endpoint": endpoint, "image_path": image_path}
