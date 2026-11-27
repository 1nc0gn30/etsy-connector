"""REST API Server & Web Cockpit for etsy-connector.

Serves on 127.0.0.1:8108 with zero external dependencies (100% Python standard library).
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import math
import mimetypes
import os
import sys
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import __version__
from .client import EtsyClient
from .mcp_server import MCP_TOOLS_DEFINITIONS
from .pod_bridge import generate_pod_payload, get_all_provider_catalogs, get_available_blueprints
from .seo_engine import audit_listing, calculate_profit
from .taxonomy import get_taxonomy_categories

MAX_BODY_BYTES = 1_048_576  # 1 MiB strict request body cap
STUDIO_ORIGIN_PORT = 3000
CSP_HEADER = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self' http://127.0.0.1:* http://localhost:*; "
    "frame-ancestors 'self' http://127.0.0.1:* http://localhost:*; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def _is_traversal_attempt(raw: str) -> bool:
    """Detect path traversal or Windows drive escapes before stripping."""
    decoded = urllib.parse.unquote(str(raw or ""))
    double_decoded = urllib.parse.unquote(decoded)
    for candidate in (str(raw or ""), decoded, double_decoded):
        norm = candidate.replace("\\", "/")
        parts = [p for p in norm.split("/") if p not in ("", ".")]
        if any(p == ".." for p in parts):
            return True
        if parts and ":" in parts[0]:
            return True
        if "\x00" in candidate:
            return True
    return False


def _safe_rel(raw: str) -> str:
    """Request path -> safe relative path inside a static dir; '' (index) if it
    tries to climb out with '..' or is absolute."""
    rel = urllib.parse.unquote(str(raw or "")).replace("\\", "/").lstrip("/")
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts) or ":" in (parts[0] if parts else ""):
        return ""
    return "/".join(parts)


def _is_valid_loopback_host(host_header: Optional[str], server_port: int) -> bool:
    """Strict loopback Host header validation against DNS rebinding."""
    if not host_header:
        return True
    raw = host_header.strip().lower()
    if not raw or any(c.isspace() for c in raw):
        return False
    allowed_hosts = {
        "127.0.0.1",
        "localhost",
        "[::1]",
        f"127.0.0.1:{server_port}",
        f"localhost:{server_port}",
        f"[::1]:{server_port}",
    }
    return raw in allowed_hosts


def _is_local_origin(origin: Optional[str], allowed_ports: Optional[Iterable[int]] = None) -> bool:
    """Strict exact-port loopback CORS Origin validation.

    No Origin header = non-browser client (CLI/curl/agent): allowed.
    Browser Origin header must match http(s)://(127.0.0.1|localhost|[::1]):<exact_allowed_port>.
    """
    if not origin:
        return True
    try:
        u = urllib.parse.urlparse(origin)
    except ValueError:
        return False
    if u.scheme not in ("http", "https"):
        return False
    if u.hostname not in ("localhost", "127.0.0.1", "::1"):
        return False
    if u.username or u.password or u.path not in ("", "/") or u.query or u.fragment:
        return False
    ports = set(allowed_ports) if allowed_ports is not None else {8108, STUDIO_ORIGIN_PORT}
    try:
        port = u.port
    except ValueError:
        return False
    return port in ports


def _default_bind_host() -> str:
    """Bind address: localhost unless explicitly opted in via $ZOTH_BIND_HOST or
    $HOST (IP literal only; zsh sets HOST to the hostname) or --host."""
    for var in ("ZOTH_BIND_HOST", "HOST"):
        val = os.environ.get(var, "").strip()
        if val == "localhost":
            return "127.0.0.1"
        if val:
            try:
                ipaddress.ip_address(val)
                return val
            except ValueError:
                pass
    return "127.0.0.1"


def _parse_finite_float(val: Any, field: str, default: Optional[float] = None) -> float:
    if val is None:
        if default is not None:
            return default
        raise ValueError(f"Field '{field}' is required")
    if isinstance(val, bool):
        raise ValueError(f"Field '{field}' must be a number, not boolean")
    try:
        num = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"Field '{field}' must be a valid number")
    if not math.isfinite(num):
        raise ValueError(f"Field '{field}' must be finite")
    return num


def _parse_strict_int(val: Any, field: str, default: Optional[int] = None) -> int:
    if val is None:
        if default is not None:
            return default
        raise ValueError(f"Field '{field}' is required")
    if isinstance(val, bool):
        raise ValueError(f"Field '{field}' must be an integer, not boolean")
    if isinstance(val, float):
        if not math.isfinite(val) or not val.is_integer():
            raise ValueError(f"Field '{field}' must be an integer")
        return int(val)
    try:
        return int(val)
    except (TypeError, ValueError):
        raise ValueError(f"Field '{field}' must be an integer")


def _parse_strict_bool(val: Any, field: str, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str) and val.lower() in ("true", "false"):
        return val.lower() == "true"
    raise ValueError(f"Field '{field}' must be a boolean")


class EtsyCockpitHandler(BaseHTTPRequestHandler):
    """Hardened HTTP Request Handler for REST API and Dual-Theme Web Cockpit."""

    server_version = f"EtsyConnectorCockpit/{__version__}"
    client: EtsyClient
    public_dir: Path
    start_time: float
    stats: Dict[str, Any]

    def log_message(self, format: str, *args: Any) -> None:
        """Silence default stdout logging."""
        return

    def _allowed_origin_ports(self) -> Tuple[int, int]:
        return (self.server.server_port, STUDIO_ORIGIN_PORT)

    def _send_security_and_cors_headers(self, include_cors: bool = True) -> None:
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Security-Policy", CSP_HEADER)
        self.send_header("Vary", "Origin")
        if include_cors:
            origin = self.headers.get("Origin")
            if origin and _is_local_origin(origin, self._allowed_origin_ports()):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, status_code: int, data: Any, head_only: bool = False, include_cors: bool = True) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_security_and_cors_headers(include_cors=include_cors)
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _guard_host_and_origin(self, head_only: bool = False) -> bool:
        """Validate Host and Origin headers before processing any request."""
        if not _is_valid_loopback_host(self.headers.get("Host"), self.server.server_port):
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"error": "Forbidden host header (loopback only)"},
                head_only=head_only,
                include_cors=False,
            )
            return False
        origin = self.headers.get("Origin")
        if origin and not _is_local_origin(origin, self._allowed_origin_ports()):
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"error": "Cross-origin request blocked (exact loopback port required)"},
                head_only=head_only,
                include_cors=False,
            )
            return False
        return True

    def do_OPTIONS(self) -> None:
        if not self._guard_host_and_origin(head_only=False):
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_security_and_cors_headers(include_cors=True)
        self.end_headers()

    def do_HEAD(self) -> None:
        self._handle_get_or_head(head_only=True)

    def do_GET(self) -> None:
        self._handle_get_or_head(head_only=False)

    def _handle_get_or_head(self, head_only: bool) -> None:
        if not self._guard_host_and_origin(head_only=head_only):
            return

        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path or "/"
        path = raw_path.rstrip("/") or "/"

        # 1. Health Probe (dynamic actual bound port)
        if path in ("/health", "/api/health"):
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "healthy",
                    "service": "etsy-connector",
                    "port": self.server.server_port,
                    "version": __version__,
                    "uptime_seconds": round(time.time() - self.start_time, 1),
                    "is_configured": self.client.is_configured(),
                    "simulation_mode": self.client.simulate,
                },
                head_only=head_only,
            )
            return

        # 2. Stats
        if path == "/api/stats":
            self._send_json(
                HTTPStatus.OK,
                {
                    "total_audits_performed": self.stats.get("audits_performed", 0),
                    "total_profit_calculations": self.stats.get("profit_calculations", 0),
                    "total_pod_payloads_generated": self.stats.get("pod_payloads_generated", 0),
                    "total_searches_executed": self.stats.get("searches_executed", 0),
                    "active_mcp_tools": len(MCP_TOOLS_DEFINITIONS),
                    "version": __version__,
                    "port": self.server.server_port,
                    "uptime_seconds": round(time.time() - self.start_time, 1),
                    "is_configured": self.client.is_configured(),
                    "simulation_mode": self.client.simulate,
                },
                head_only=head_only,
            )
            return

        # 3. Taxonomy Categories
        if path == "/api/taxonomy":
            self._send_json(
                HTTPStatus.OK,
                {"categories": get_taxonomy_categories()},
                head_only=head_only,
            )
            return

        # 4. MCP Tools List
        if path == "/api/mcp/tools":
            self._send_json(
                HTTPStatus.OK,
                {
                    "tools": MCP_TOOLS_DEFINITIONS,
                    "count": len(MCP_TOOLS_DEFINITIONS),
                },
                head_only=head_only,
            )
            return

        # 5. Blueprints List (Printify + Gelato)
        if path == "/api/blueprints":
            qs = urllib.parse.parse_qs(parsed.query)
            prov = (qs.get("provider", [""])[0] or "").strip().lower()
            if prov in ("printify", "gelato"):
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "provider": prov,
                        "blueprints": get_available_blueprints(prov),
                    },
                    head_only=head_only,
                )
            else:
                catalogs = get_all_provider_catalogs()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "blueprints": catalogs["printify"],
                        "providers": catalogs,
                    },
                    head_only=head_only,
                )
            return

        # 6. Path traversal rejection BEFORE _safe_rel normalization
        if _is_traversal_attempt(raw_path):
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"error": "Path traversal blocked"},
                head_only=head_only,
            )
            return

        # 7. Static files
        rel_file = _safe_rel(raw_path)
        public_root = self.public_dir.resolve()
        if rel_file == "" or rel_file == "index.html":
            target = public_root / "index.html"
        else:
            target = public_root / rel_file

        try:
            target = target.resolve()
            if not target.is_relative_to(public_root):
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "Access denied"}, head_only=head_only)
                return
        except Exception:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "File not found"}, head_only=head_only)
            return

        if target.exists() and target.is_file():
            mime, _ = mimetypes.guess_type(str(target))
            if not mime:
                if target.suffix == ".js":
                    mime = "application/javascript; charset=utf-8"
                elif target.suffix == ".css":
                    mime = "text/css; charset=utf-8"
                elif target.suffix == ".html":
                    mime = "text/html; charset=utf-8"
                elif target.suffix == ".svg":
                    mime = "image/svg+xml"
                else:
                    mime = "application/octet-stream"
            elif mime.startswith("text/") or mime in ("application/javascript", "application/xml", "application/json"):
                mime = f"{mime}; charset=utf-8"

            content = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self._send_security_and_cors_headers(include_cors=True)
            self.end_headers()
            if not head_only:
                self.wfile.write(content)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Resource not found", "path": raw_path}, head_only=head_only)

    def do_POST(self) -> None:
        if not self._guard_host_and_origin(head_only=False):
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        raw_cl = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_cl)
        except (TypeError, ValueError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Content-Length header"})
            return
        if length < 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Negative Content-Length header"})
            return
        if length > MAX_BODY_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": f"Payload exceeds {MAX_BODY_BYTES} byte limit"},
            )
            return

        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return

        if not isinstance(data, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "JSON body must be an object"})
            return

        try:
            # 1. Audit Listing
            if path == "/api/audit":
                title = data.get("title", "")
                tags = data.get("tags", [])
                desc = data.get("description", "")
                if not isinstance(title, str) or not isinstance(desc, str):
                    raise ValueError("Fields 'title' and 'description' must be strings")
                if not isinstance(tags, list):
                    raise ValueError("Field 'tags' must be an array of strings")
                result = audit_listing(title=title, tags=tags, description=desc)
                self.stats["audits_performed"] = self.stats.get("audits_performed", 0) + 1
                self._send_json(HTTPStatus.OK, result)
                return

            # 2. Profit Calculation
            if path == "/api/profit":
                retail = _parse_finite_float(data.get("retail_price"), "retail_price", default=34.99)
                pod = _parse_finite_float(data.get("pod_base_cost"), "pod_base_cost", default=12.80)
                ship_chg = _parse_finite_float(data.get("shipping_charged"), "shipping_charged", default=0.0)
                ship_cost = _parse_finite_float(data.get("shipping_cost"), "shipping_cost", default=0.0)
                ads = _parse_strict_bool(data.get("is_offsite_ads"), "is_offsite_ads", default=False)
                raw_rate = data.get("offsite_ads_rate")
                ads_rate = _parse_finite_float(raw_rate, "offsite_ads_rate") if raw_rate is not None else None
                calc = calculate_profit(
                    retail,
                    pod,
                    ship_chg,
                    ship_cost,
                    is_offsite_ads=ads,
                    offsite_ads_rate=ads_rate,
                )
                self.stats["profit_calculations"] = self.stats.get("profit_calculations", 0) + 1
                self._send_json(HTTPStatus.OK, calc)
                return

            # 3. Search Listings
            if path == "/api/search":
                kw = data.get("keywords", "wildflower sweatshirt")
                if not isinstance(kw, str):
                    raise ValueError("Field 'keywords' must be a string")
                limit = _parse_strict_int(data.get("limit"), "limit", default=10)
                min_p = _parse_finite_float(data.get("min_price"), "min_price") if data.get("min_price") is not None else None
                max_p = _parse_finite_float(data.get("max_price"), "max_price") if data.get("max_price") is not None else None
                res = self.client.search_listings(keywords=kw, limit=limit, min_price=min_p, max_price=max_p)
                self.stats["searches_executed"] = self.stats.get("searches_executed", 0) + 1
                self._send_json(HTTPStatus.OK, res)
                return

            # 4. Generate POD Payload (Printify or Gelato)
            if path == "/api/pod":
                bp = str(data.get("blueprint_key", "comfort_colors_1717"))
                provider = str(data.get("provider", "printify"))
                title = data.get("title", "")
                desc = data.get("description", "")
                tags = data.get("tags", [])
                img = data.get("design_image_url", "https://assets.nullai.tech/sample_wildflower.png")
                if not isinstance(title, str) or not isinstance(desc, str) or not isinstance(img, str):
                    raise ValueError("Fields 'title', 'description', and 'design_image_url' must be strings")
                if not isinstance(tags, list):
                    raise ValueError("Field 'tags' must be an array")
                raw_price = data.get("retail_price_usd")
                price = _parse_finite_float(raw_price, "retail_price_usd") if raw_price is not None else None
                payload = generate_pod_payload(
                    blueprint_key=bp,
                    title=title,
                    description=desc,
                    tags=tags,
                    design_image_url=img,
                    retail_price_usd=price,
                    provider=provider,
                )
                self.stats["pod_payloads_generated"] = self.stats.get("pod_payloads_generated", 0) + 1
                self._send_json(HTTPStatus.OK, payload)
                return

            # 5. Create Draft Listing
            if path == "/api/create-draft":
                title = data.get("title", "New Etsy Listing")
                desc = data.get("description", "")
                if not isinstance(title, str) or not isinstance(desc, str):
                    raise ValueError("Fields 'title' and 'description' must be strings")
                tags = data.get("tags", [])
                if not isinstance(tags, list):
                    raise ValueError("Field 'tags' must be an array")
                price = _parse_finite_float(data.get("price"), "price", default=34.99)
                quantity = _parse_strict_int(data.get("quantity"), "quantity", default=999)
                taxonomy_id = _parse_strict_int(data.get("taxonomy_id"), "taxonomy_id", default=1099)
                who_made = str(data.get("who_made", "i_did"))
                when_made = str(data.get("when_made", "2020_2026"))
                is_supply = _parse_strict_bool(data.get("is_supply"), "is_supply", default=False)
                listing_type = str(data.get("listing_type", "download"))
                confirm = _parse_strict_bool(data.get("confirm"), "confirm", default=False)
                res = self.client.create_draft_listing(
                    title=title,
                    description=desc,
                    price=price,
                    quantity=quantity,
                    tags=tags,
                    taxonomy_id=taxonomy_id,
                    who_made=who_made,
                    when_made=when_made,
                    is_supply=is_supply,
                    listing_type=listing_type,
                    confirm=confirm,
                )
                self._send_json(HTTPStatus.OK, res)
                return

            # 6. Save Credentials
            if path == "/api/credentials":
                api_key = data.get("api_key", "")
                access_token = data.get("access_token", "")
                shop_id = data.get("shop_id", "me")
                if not isinstance(api_key, str) or not isinstance(access_token, str) or not isinstance(shop_id, str):
                    raise ValueError("Credential fields must be strings")
                self.client.save_credentials(api_key, access_token, shop_id)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "credentials_saved",
                        "is_configured": self.client.is_configured(),
                        "simulation_mode": self.client.simulate,
                    },
                )
                return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except RuntimeError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found", "path": parsed.path})


def run_server(port: int = 8108, public_dir: Optional[Path] = None, host: Optional[str] = None) -> None:
    """Run Etsy Connector REST API and Web Cockpit."""
    p_dir = public_dir or (Path(__file__).resolve().parent.parent.parent / "public")
    EtsyCockpitHandler.public_dir = p_dir
    EtsyCockpitHandler.client = EtsyClient()
    EtsyCockpitHandler.start_time = time.time()
    EtsyCockpitHandler.stats = {
        "audits_performed": 0,
        "profit_calculations": 0,
        "pod_payloads_generated": 0,
        "searches_executed": 0,
    }

    bind_host = host or _default_bind_host()
    server = ThreadingHTTPServer((bind_host, port), EtsyCockpitHandler)
    sys.stderr.write(f"[etsy-connector] v{__version__} Web Cockpit active on http://{bind_host}:{server.server_port}\n")
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    finally:
        server.server_close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Etsy Connector Loopback REST API & Web Cockpit")
    parser.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8108, help="Bind port (default: 8108)")
    args = parser.parse_args(argv)
    run_server(port=args.port, host=args.host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
