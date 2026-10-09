"""REST API Server & Web Cockpit for etsy-connector.

Serves on port 8107 with zero external dependencies (100% Python standard library).
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import EtsyClient
from .mcp_server import MCP_TOOLS_DEFINITIONS
from .pod_bridge import generate_printify_product_payload, get_available_blueprints
from .seo_engine import audit_listing, calculate_profit
from .taxonomy import find_taxonomy, get_taxonomy_categories

FLIGHT_RECORDER_URL = "http://127.0.0.1:8104/api/ingest"
NEURO_MEMORY_URL = "http://127.0.0.1:8094/api/memories"


class EtsyCockpitHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for REST API and Glassmorphic Cockpit."""

    server_version = "EtsyConnectorCockpit/0.1.0"
    client: EtsyClient
    public_dir: Path
    start_time: float
    stats: Dict[str, Any]

    def log_message(self, format: str, *args: Any) -> None:
        """Silence default stdout logging."""
        return

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")

    def _send_json(self, status_code: int, data: Any) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "":
            path = "/"

        # 1. Health Probe
        if path in ("/health", "/api/health"):
            self._send_json(HTTPStatus.OK, {
                "status": "healthy",
                "service": "etsy-connector",
                "port": 8108,
                "version": "0.1.0",
                "uptime_seconds": round(time.time() - self.start_time, 1),
                "is_configured": self.client.is_configured(),
                "simulation_mode": self.client.simulate,
            })
            return

        # 2. Stats
        if path == "/api/stats":
            self._send_json(HTTPStatus.OK, {
                "total_audits_performed": self.stats.get("audits_performed", 0),
                "total_profit_calculations": self.stats.get("profit_calculations", 0),
                "total_pod_payloads_generated": self.stats.get("pod_payloads_generated", 0),
                "total_searches_executed": self.stats.get("searches_executed", 0),
                "active_mcp_tools": len(MCP_TOOLS_DEFINITIONS),
                "uptime_seconds": round(time.time() - self.start_time, 1),
                "is_configured": self.client.is_configured(),
                "simulation_mode": self.client.simulate,
            })
            return

        # 3. Taxonomy Categories
        if path == "/api/taxonomy":
            self._send_json(HTTPStatus.OK, {
                "categories": get_taxonomy_categories(),
            })
            return

        # 4. MCP Tools List
        if path == "/api/mcp/tools":
            self._send_json(HTTPStatus.OK, {
                "tools": MCP_TOOLS_DEFINITIONS,
                "count": len(MCP_TOOLS_DEFINITIONS),
            })
            return

        # 5. Blueprints List
        if path == "/api/blueprints":
            self._send_json(HTTPStatus.OK, {
                "blueprints": get_available_blueprints(),
            })
            return

        # 6. Static files
        rel_file = parsed.path.lstrip("/")
        if rel_file == "" or rel_file == "index.html":
            target = self.public_dir / "index.html"
        else:
            target = self.public_dir / rel_file

        try:
            target = target.resolve()
            if not str(target).startswith(str(self.public_dir.resolve())):
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "Access denied"})
                return
        except Exception:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "File not found"})
            return

        if target.exists() and target.is_file():
            mime, _ = mimetypes.guess_type(str(target))
            if not mime:
                if target.suffix == ".js":
                    mime = "application/javascript"
                elif target.suffix == ".css":
                    mime = "text/css"
                elif target.suffix == ".html":
                    mime = "text/html"
                else:
                    mime = "application/octet-stream"

            content = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Resource not found", "path": parsed.path})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return

        # 1. Audit Listing
        if path == "/api/audit":
            title = data.get("title", "")
            tags = data.get("tags", [])
            desc = data.get("description", "")
            result = audit_listing(title=title, tags=tags, description=desc)
            self.stats["audits_performed"] = self.stats.get("audits_performed", 0) + 1
            self._notify_flight_recorder("ETSY_SEO_AUDIT", f"Audited listing '{title[:30]}...' Score: {result['overall_score']}")
            self._send_json(HTTPStatus.OK, result)
            return

        # 2. Profit Calculation
        if path == "/api/profit":
            retail = float(data.get("retail_price", 34.99))
            pod = float(data.get("pod_base_cost", 12.80))
            ship_chg = float(data.get("shipping_charged", 0.0))
            ship_cost = float(data.get("shipping_cost", 0.0))
            ads = bool(data.get("is_offsite_ads", False))
            calc = calculate_profit(retail, pod, ship_chg, ship_cost, ads)
            self.stats["profit_calculations"] = self.stats.get("profit_calculations", 0) + 1
            self._send_json(HTTPStatus.OK, calc)
            return

        # 3. Search Listings
        if path == "/api/search":
            kw = data.get("keywords", "wildflower sweatshirt")
            limit = int(data.get("limit", 10))
            res = self.client.search_listings(keywords=kw, limit=limit)
            self.stats["searches_executed"] = self.stats.get("searches_executed", 0) + 1
            self._send_json(HTTPStatus.OK, res)
            return

        # 4. Generate POD Payload
        if path == "/api/pod":
            bp = data.get("blueprint_key", "comfort_colors_1717")
            title = data.get("title", "")
            desc = data.get("description", "")
            tags = data.get("tags", [])
            img = data.get("design_image_url", "https://assets.nullai.tech/sample_wildflower.png")
            price = data.get("retail_price_usd")
            payload = generate_printify_product_payload(bp, title, desc, tags, img, price)
            self.stats["pod_payloads_generated"] = self.stats.get("pod_payloads_generated", 0) + 1
            self._send_json(HTTPStatus.OK, payload)
            return

        # 5. Save Credentials
        if path == "/api/credentials":
            api_key = data.get("api_key", "")
            access_token = data.get("access_token", "")
            shop_id = data.get("shop_id", "")
            self.client.save_credentials(api_key, access_token, shop_id)
            self._send_json(HTTPStatus.OK, {
                "status": "credentials_saved",
                "is_configured": self.client.is_configured(),
                "simulation_mode": self.client.simulate,
            })
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found", "path": parsed.path})

    def _notify_flight_recorder(self, event_type: str, detail: str) -> None:
        """Asynchronously send telemetry to agent-flight-recorder (:8104)."""
        def _send() -> None:
            try:
                payload = json.dumps({
                    "session_id": "flt-etsy-connector",
                    "event_type": event_type,
                    "severity": "INFO",
                    "payload": {"detail": detail, "timestamp": time.time()},
                }).encode("utf-8")
                req = urllib.request.Request(
                    FLIGHT_RECORDER_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=1.0):
                    pass
            except Exception:
                pass
        threading.Thread(target=_send, daemon=True).start()


def run_server(port: int = 8108, public_dir: Optional[Path] = None) -> None:
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

    server = ThreadingHTTPServer(("0.0.0.0", port), EtsyCockpitHandler)
    sys.stderr.write(f"[etsy-connector] Web Cockpit active on http://127.0.0.1:{port}\n")
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
