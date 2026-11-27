"""Etsy Open API v3 Client with Resilient Simulation Mode.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__

CONFIG_PATH = Path.home() / ".etsy_connector_config.json"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8108/oauth/callback"
USER_AGENT = f"AntigravityEtsyConnector/{__version__}"

_EXT_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
}


def _quote_path_segment(value: Any, label: str) -> str:
    """Validate and URL-quote a path segment (shop_id or listing_id)."""
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{label} cannot be empty")
    if any(ch in raw for ch in ("/", "\\", "\r", "\n", "\x00")) or ".." in raw:
        raise ValueError(f"Invalid {label}: contains disallowed path characters")
    return urllib.parse.quote(raw, safe="")


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe HTTP Content-Disposition header inclusion."""
    base = os.path.basename(str(filename or "upload.bin"))
    cleaned = re.sub(r'["\\\r\n\x00/]', "_", base).strip()
    return cleaned or "upload.bin"


def _detect_mime_type(file_path: str, default: str = "application/octet-stream") -> str:
    """Infer MIME type strictly from file extension."""
    ext = Path(file_path).suffix.lower()
    return _EXT_MIME_MAP.get(ext, default)


class EtsyClient:
    """Etsy Open API v3 HTTP client with transparent simulation mode."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        shop_id: Optional[str] = None,
        simulate: Optional[bool] = None,
    ) -> None:
        config = self._load_config()
        self.api_key = api_key or os.environ.get("ETSY_API_KEY") or config.get("api_key", "")
        self.access_token = access_token or os.environ.get("ETSY_ACCESS_TOKEN") or config.get("access_token", "")
        self.shop_id = shop_id or os.environ.get("ETSY_SHOP_ID") or config.get("shop_id", "")

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

    def save_credentials(
        self,
        api_key: str,
        access_token: str,
        shop_id: str,
        refresh_token: Optional[str] = None,
    ) -> None:
        """Persist API credentials to user config file (atomic 0600)."""
        existing = self._load_config()
        self.api_key = str(api_key).strip()
        self.access_token = str(access_token).strip()
        self.shop_id = str(shop_id).strip() or "me"
        self.simulate = not (self.api_key and self.access_token)
        existing.update(
            {
                "api_key": self.api_key,
                "access_token": self.access_token,
                "shop_id": self.shop_id,
                "updated_at": time.time(),
            }
        )
        if refresh_token:
            existing["refresh_token"] = str(refresh_token).strip()
        data = json.dumps(existing, indent=2)
        tmp = CONFIG_PATH.with_name(CONFIG_PATH.name + ".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.chmod(tmp, 0o600)
        os.replace(tmp, CONFIG_PATH)

    def refresh_oauth_token(self, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """Refresh an expired Etsy OAuth 2.0 access_token using refresh_token."""
        cfg = self._load_config()
        client_id = (self.api_key or cfg.get("api_key", "")).split(":")[0].strip()
        rt = (refresh_token or cfg.get("refresh_token", "")).strip()
        if not client_id or not rt:
            raise ValueError("Missing client_id or refresh_token for Etsy OAuth refresh.")

        payload = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": rt,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://api.etsy.com/v3/public/oauth/token",
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))

        new_access = token_data.get("access_token", "")
        new_refresh = token_data.get("refresh_token", rt)
        self.save_credentials(
            api_key=self.api_key or cfg.get("api_key", client_id),
            access_token=new_access,
            shop_id=str(self.shop_id or cfg.get("shop_id") or os.environ.get("ETSY_SHOP_ID") or "me"),
            refresh_token=new_refresh,
        )
        return token_data

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
            "User-Agent": USER_AGENT,
        }

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            if e.code in (401, 403) and method == "GET":
                return self._simulate_response(
                    endpoint, method, params, payload, note=f"Live API error ({e.code}); fell back to simulation."
                )
            raise RuntimeError(f"Etsy API HTTP {e.code}: {err_body[:500]}")
        except Exception as e:
            if method == "GET":
                return self._simulate_response(
                    endpoint, method, params, payload, note=f"Network error ({type(e).__name__}); fell back to simulation."
                )
            raise RuntimeError(f"Etsy API request failed ({type(e).__name__}); nothing was created.") from None

    def _simulate_response(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate deterministic simulated responses for testing and offline development."""
        sim_id = f"etsy_sim_{uuid.uuid4().hex[:8]}"

        if "/shops/" in endpoint and endpoint.endswith("/listings"):
            p = payload or {}
            return {
                "simulation": True,
                "status": "draft",
                "listing_id": 1827495000 + int(time.time() % 100000),
                "title": p.get("title", "Simulated Etsy Listing"),
                "description": p.get("description", ""),
                "state": "draft",
                "price": {"amount": int(round((p.get("price", 34.99) or 34.99) * 100)), "divisor": 100, "currency_code": "USD"},
                "quantity": p.get("quantity", 999),
                "tags": p.get("tags", []),
                "taxonomy_id": p.get("taxonomy_id", 1099),
                "url": f"https://www.etsy.com/listing/simulated/{sim_id}",
                "created_timestamp": int(time.time()),
                "note": note or "Simulated Etsy draft listing created (Live API Key not active).",
            }

        if "/listings/active" in endpoint:
            kw = (params or {}).get("keywords", "wildflower sweatshirt")
            mock_results = [
                {
                    "listing_id": 1782349011,
                    "title": "Botanical Wildflower Embroidered Crewneck Sweatshirt, Cozy Cottagecore Gift, Heavy Blend Pullover",
                    "price": {"amount": 3699, "divisor": 100, "currency_code": "USD"},
                    "tags": ["wildflower crewneck", "garden sweatshirt", "cottagecore gift", "botanical shirt", "mothers day gift", "comfort colors 1717", "plant lover gift"],
                    "views": 4820,
                    "num_favorers": 1240,
                    "shop_name": "BotanicalHavenPrints",
                    "rating": 4.95,
                },
                {
                    "listing_id": 1782349012,
                    "title": "Vintage Songbird Watercolor Ceramic Coffee Mug 15oz, Backyard Birdwatcher Tea Cup, Country Kitchen Decor",
                    "price": {"amount": 2199, "divisor": 100, "currency_code": "USD"},
                    "tags": ["songbird mug", "birdwatcher gift", "watercolor tea cup", "ceramic mug 15oz", "coffee lover gift", "botanical mug"],
                    "views": 2910,
                    "num_favorers": 820,
                    "shop_name": "MorningMeadowStudio",
                    "rating": 4.98,
                },
                {
                    "listing_id": 1782349013,
                    "title": "Heavyweight Canvas Farmers Market Tote Bag, French Lavender & Herb Botanical Grocery Bag, Library Book Tote",
                    "price": {"amount": 2499, "divisor": 100, "currency_code": "USD"},
                    "tags": ["canvas tote bag", "farmers market", "lavender tote", "french botanical", "library tote", "eco market bag"],
                    "views": 1840,
                    "num_favorers": 490,
                    "shop_name": "HeirloomLivingCo",
                    "rating": 4.92,
                },
            ]
            limit = max(1, min(int((params or {}).get("limit", 10)), 100))
            return {
                "simulation": True,
                "count": len(mock_results[:limit]),
                "results": mock_results[:limit],
                "keywords": kw,
                "note": note or "Simulated Etsy search results for competitor & niche keyword intelligence.",
            }

        if "/shops/" in endpoint:
            return {
                "simulation": True,
                "shop_id": self.shop_id or "me",
                "shop_name": "SampleBotanicalShop",
                "title": "Botanical Apparel, Ceramic Mugs & Printable Wall Art",
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
        target_shop = _quote_path_segment(shop_id or self.shop_id or "me", "shop_id")
        return self._request(f"/shops/{target_shop}")

    def search_listings(
        self,
        keywords: str,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Search active Etsy listings for competitor analysis, keywords, and prices."""
        params: Dict[str, Any] = {"keywords": keywords, "limit": max(1, min(int(limit), 100))}
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
        who_made: str = "i_did",
        when_made: str = "2020_2026",
        is_supply: bool = False,
        listing_type: str = "download",
        confirm: bool = False,
    ) -> Dict[str, Any]:
        """Create a draft listing on Etsy (dry-run by default when live credentials exist)."""
        target_shop = _quote_path_segment(self.shop_id or "me", "shop_id")
        payload = {
            "quantity": int(quantity),
            "title": str(title)[:140],
            "description": str(description),
            "price": round(float(price), 2),
            "who_made": who_made,
            "when_made": when_made,
            "taxonomy_id": int(taxonomy_id),
            "is_supply": bool(is_supply),
            "type": listing_type,
            "tags": [str(t)[:20] for t in (tags or [])][:13],
            "state": "draft",
        }
        if not self.simulate and not (confirm or os.environ.get("ETSY_ALLOW_LIVE_WRITES") == "1"):
            return {
                "dry_run": True,
                "simulation": False,
                "status": "not_sent",
                "message": "Live credentials present: pass confirm=true (or set ETSY_ALLOW_LIVE_WRITES=1) to create this draft on Etsy.",
                "endpoint": f"POST /shops/{target_shop}/listings",
                "payload": payload,
            }
        return self._request(f"/shops/{target_shop}/listings", method="POST", payload=payload)

    def update_shop(
        self,
        title: Optional[str] = None,
        announcement: Optional[str] = None,
        sale_message: Optional[str] = None,
        digital_sale_message: Optional[str] = None,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        """Update Etsy shop metadata via PUT /v3/application/shops/{shop_id}."""
        target_shop = _quote_path_segment(self.shop_id or "me", "shop_id")
        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if announcement is not None:
            payload["announcement"] = announcement
        if sale_message is not None:
            payload["sale_message"] = sale_message
        if digital_sale_message is not None:
            payload["digital_sale_message"] = digital_sale_message

        if self.simulate or not self.is_configured():
            return {
                "simulation": True,
                "status": "updated",
                "shop_id": target_shop,
                "updated_fields": payload,
                "note": "Simulated shop profile update (configure live API key + OAuth token to push live).",
            }

        if not (confirm or os.environ.get("ETSY_ALLOW_LIVE_WRITES") == "1"):
            return {
                "dry_run": True,
                "simulation": False,
                "status": "not_sent",
                "endpoint": f"PUT /shops/{target_shop}",
                "payload": payload,
            }
        return self._request(f"/shops/{target_shop}", method="PUT", payload=payload)

    def _multipart_upload(
        self,
        endpoint: str,
        file_field: str,
        file_path: str,
        mime_type: str,
        extra_fields: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Perform standard-library multipart/form-data upload to Etsy Open API v3."""
        boundary = f"----AntigravityEtsyBoundary{uuid.uuid4().hex}"
        body = bytearray()
        for k, v in (extra_fields or {}).items():
            safe_k = _sanitize_filename(k)
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{safe_k}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{v}\r\n".encode("utf-8"))

        filename = _sanitize_filename(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{_sanitize_filename(file_field)}"; filename="{filename}"\r\n'.encode("utf-8")
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

        url = f"{self.base_url}{endpoint}"
        headers = {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": USER_AGENT,
        }
        req = urllib.request.Request(url, data=bytes(body), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def upload_listing_image(
        self,
        listing_id: str,
        image_path: str,
        rank: int = 1,
        alt_text: Optional[str] = None,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        """Upload product mockup or design image to Etsy listing (dry-run by default in live mode)."""
        safe_listing = _quote_path_segment(listing_id, "listing_id")
        target_shop = _quote_path_segment(self.shop_id or "me", "shop_id")
        mime_type = _detect_mime_type(image_path, default="image/png")
        safe_name = _sanitize_filename(image_path)

        if self.simulate or not self.is_configured():
            return {
                "simulation": True,
                "status": "uploaded",
                "listing_id": safe_listing,
                "image_id": f"img_{uuid.uuid4().hex[:8]}",
                "filename": safe_name,
                "mime_type": mime_type,
                "rank": int(rank),
                "url_570xN": f"https://i.etsystatic.com/simulated/{safe_listing}_570xN.jpg",
                "url_fullxfull": f"https://i.etsystatic.com/simulated/{safe_listing}_fullxfull.jpg",
            }

        endpoint = f"/shops/{target_shop}/listings/{safe_listing}/images"
        fields = {"rank": str(int(rank))}
        if alt_text:
            fields["alt_text"] = str(alt_text)[:250]

        if not (confirm or os.environ.get("ETSY_ALLOW_LIVE_WRITES") == "1"):
            return {
                "dry_run": True,
                "simulation": False,
                "status": "not_sent",
                "message": "Live credentials present: pass confirm=true (or set ETSY_ALLOW_LIVE_WRITES=1) to upload this image to Etsy.",
                "endpoint": f"POST {endpoint}",
                "filename": safe_name,
                "mime_type": mime_type,
                "fields": fields,
            }
        return self._multipart_upload(endpoint, "image", image_path, mime_type, fields)

    def upload_listing_file(
        self,
        listing_id: str,
        file_path: str,
        name: Optional[str] = None,
        rank: int = 1,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        """Upload instant digital download file (PDF, ZIP, PNG) to an Etsy listing (dry-run by default in live mode)."""
        safe_listing = _quote_path_segment(listing_id, "listing_id")
        target_shop = _quote_path_segment(self.shop_id or "me", "shop_id")
        filename = _sanitize_filename(name or os.path.basename(file_path))
        mime_type = _detect_mime_type(file_path, default="application/octet-stream")

        if self.simulate or not self.is_configured():
            return {
                "simulation": True,
                "status": "uploaded",
                "listing_id": safe_listing,
                "listing_file_id": int(time.time() % 1000000),
                "filename": filename,
                "mime_type": mime_type,
                "rank": int(rank),
                "note": "Simulated digital download attachment uploaded.",
            }

        endpoint = f"/shops/{target_shop}/listings/{safe_listing}/files"
        fields = {"name": filename, "rank": str(int(rank))}

        if not (confirm or os.environ.get("ETSY_ALLOW_LIVE_WRITES") == "1"):
            return {
                "dry_run": True,
                "simulation": False,
                "status": "not_sent",
                "message": "Live credentials present: pass confirm=true (or set ETSY_ALLOW_LIVE_WRITES=1) to upload this file to Etsy.",
                "endpoint": f"POST {endpoint}",
                "filename": filename,
                "mime_type": mime_type,
                "fields": fields,
            }
        return self._multipart_upload(endpoint, "file", file_path, mime_type, fields)

    @staticmethod
    def generate_oauth_pkce(
        api_key: str,
        redirect_uri: Optional[str] = None,
        scopes: str = "listings_r listings_w shops_r shops_w transactions_r",
    ) -> Dict[str, str]:
        """Generate OAuth 2.0 PKCE verifier, challenge, and authorization URL for Etsy API v3."""
        import base64
        import hashlib
        import secrets

        resolved_redirect = (
            redirect_uri
            or os.environ.get("ETSY_REDIRECT_URI")
            or DEFAULT_REDIRECT_URI
        ).strip()
        client_id = api_key.split(":")[0].strip()
        verifier = secrets.token_urlsafe(32)
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        state = secrets.token_hex(8)

        params = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": resolved_redirect,
                "scope": scopes,
                "client_id": client_id,
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        result = {
            "auth_url": f"https://www.etsy.com/oauth/connect?{params}",
            "code_verifier": verifier,
            "code_challenge": challenge,
            "state": state,
            "redirect_uri": resolved_redirect,
            "client_id": client_id,
        }
        existing: Dict[str, Any] = {}
        if CONFIG_PATH.exists():
            try:
                existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        existing.update(
            {
                "api_key": api_key.strip(),
                "client_id": client_id,
                "code_verifier": verifier,
                "redirect_uri": resolved_redirect,
                "state": state,
                "shop_id": existing.get("shop_id") or os.environ.get("ETSY_SHOP_ID") or "me",
                "updated_at": time.time(),
            }
        )
        tmp = CONFIG_PATH.with_name(CONFIG_PATH.name + ".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(existing, indent=2))
        os.chmod(tmp, 0o600)
        os.replace(tmp, CONFIG_PATH)
        return result

    def exchange_oauth_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exchange OAuth 2.0 authorization code for an Etsy access_token and refresh_token."""
        cfg = self._load_config()
        client_id = (self.api_key or cfg.get("api_key", "")).split(":")[0].strip()
        verifier = code_verifier or cfg.get("code_verifier", "")
        redirect = (
            redirect_uri
            or cfg.get("redirect_uri")
            or os.environ.get("ETSY_REDIRECT_URI")
            or DEFAULT_REDIRECT_URI
        )

        if not client_id or not verifier:
            raise ValueError("Missing client_id or code_verifier. Run 'etsy-connector auth --key <KEY>' first.")

        payload = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect,
                "code": code.strip(),
                "code_verifier": verifier,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://api.etsy.com/v3/public/oauth/token",
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))

        access_token = token_data.get("access_token", "")
        refresh_tok = token_data.get("refresh_token", "")
        self.save_credentials(
            api_key=cfg.get("api_key", client_id),
            access_token=access_token,
            shop_id=str(cfg.get("shop_id") or os.environ.get("ETSY_SHOP_ID") or "me"),
            refresh_token=refresh_tok,
        )
        return token_data
