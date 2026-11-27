"""Comprehensive REST API, security, POD, and profit regression tests for etsy-connector v2.6.0."""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from etsy_connector.client import EtsyClient
from etsy_connector.seo_engine import calculate_profit
from etsy_connector.web_cockpit import EtsyCockpitHandler, MAX_BODY_BYTES


class TestEtsyApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public_dir = Path(__file__).resolve().parent.parent / "public"
        EtsyCockpitHandler.public_dir = cls.public_dir
        EtsyCockpitHandler.client = EtsyClient(simulate=True)
        EtsyCockpitHandler.start_time = time.time()
        EtsyCockpitHandler.stats = {
            "audits_performed": 0,
            "profit_calculations": 0,
            "pod_payloads_generated": 0,
            "searches_executed": 0,
        }
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), EtsyCockpitHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _raw_request(self, method: str, path: str, body: bytes | None = None, headers: dict | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3.0)
        try:
            try:
                conn.request(method, path, body=body, headers=headers or {})
            except (BrokenPipeError, ConnectionResetError):
                pass
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, dict(resp.getheaders()), data
        finally:
            conn.close()

    def test_health_endpoint_dynamic_port_and_headers(self):
        status, headers, body = self._raw_request("GET", "/health")
        self.assertEqual(status, 200)
        data = json.loads(body.decode())
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "etsy-connector")
        self.assertEqual(data["port"], self.port)
        self.assertEqual(data["version"], "2.6.0")
        hdrs_lower = {k.lower(): v for k, v in headers.items()}
        self.assertEqual(hdrs_lower.get("x-frame-options"), "SAMEORIGIN")
        self.assertEqual(hdrs_lower.get("x-content-type-options"), "nosniff")
        self.assertEqual(hdrs_lower.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertIn("frame-ancestors 'self' http://127.0.0.1:* http://localhost:*", hdrs_lower.get("content-security-policy", ""))
        self.assertEqual(hdrs_lower.get("vary"), "Origin")

    def test_head_endpoints(self):
        for route in ("/", "/health", "/api/health", "/api/stats", "/api/taxonomy", "/api/blueprints", "/api/mcp/tools"):
            status, headers, body = self._raw_request("HEAD", route)
            self.assertEqual(status, 200, route)
            self.assertEqual(body, b"", route)
            hdrs_lower = {k.lower(): v for k, v in headers.items()}
            self.assertEqual(hdrs_lower.get("x-content-type-options"), "nosniff")

    def test_dns_rebinding_host_rejected(self):
        for method in ("GET", "HEAD", "OPTIONS"):
            status, _, _ = self._raw_request(method, "/health", headers={"Host": "evil.example.invalid"})
            self.assertEqual(status, 403, method)
        status, _, _ = self._raw_request(
            "POST",
            "/api/audit",
            body=b'{"title":"test","tags":[]}',
            headers={"Host": "evil.example.invalid", "Content-Type": "application/json"},
        )
        self.assertEqual(status, 403)

    def test_cors_exact_port_and_evil_origin_blocked(self):
        spoofed = f"http://127.0.0.1:{self.port}0"
        for bad_origin in (spoofed, "https://evil.example"):
            for method, path in (("GET", "/health"), ("HEAD", "/health"), ("OPTIONS", "/api/audit"), ("POST", "/api/audit")):
                body = b'{"title":"t","tags":[]}' if method == "POST" else None
                hdrs = {"Origin": bad_origin, "Content-Type": "application/json"}
                status, resp_hdrs, _ = self._raw_request(method, path, body=body, headers=hdrs)
                self.assertEqual(status, 403, f"{method} {bad_origin}")
                self.assertNotIn("Access-Control-Allow-Origin", resp_hdrs)

        good_origin = f"http://127.0.0.1:{self.port}"
        status, resp_hdrs, _ = self._raw_request("GET", "/health", headers={"Origin": good_origin})
        self.assertEqual(status, 200)
        hdrs_lower = {k.lower(): v for k, v in resp_hdrs.items()}
        self.assertEqual(hdrs_lower.get("access-control-allow-origin"), good_origin)
        self.assertEqual(hdrs_lower.get("vary"), "Origin")

    def test_path_traversal_returns_403(self):
        for path in ("/../server.py", "/%2e%2e/server.py", "/..%2fserver.py"):
            status, _, _ = self._raw_request("GET", path)
            self.assertEqual(status, 403, path)

    def test_body_cap_413_and_bad_content_length_400(self):
        oversized = b'{"title":"' + (b"a" * (MAX_BODY_BYTES + 128)) + b'"}'
        status, _, _ = self._raw_request(
            "POST",
            "/api/audit",
            body=oversized,
            headers={"Content-Type": "application/json", "Content-Length": str(len(oversized))},
        )
        self.assertEqual(status, 413)

        status, _, _ = self._raw_request(
            "POST",
            "/api/audit",
            body=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "-5"},
        )
        self.assertEqual(status, 400)

    def test_malformed_non_dict_and_bad_types_return_400(self):
        cases = [
            ("/api/audit", b"{bad json"),
            ("/api/audit", b"[1, 2, 3]"),
            ("/api/audit", b'"just a string"'),
            ("/api/profit", json.dumps({"retail_price": "notanumber", "pod_base_cost": 10}).encode()),
            ("/api/profit", json.dumps({"retail_price": float("inf"), "pod_base_cost": 10}).encode()),
            ("/api/search", json.dumps({"keywords": "mug", "limit": "bad"}).encode()),
        ]
        for path, payload in cases:
            status, _, body = self._raw_request(
                "POST", path, body=payload, headers={"Content-Type": "application/json"}
            )
            self.assertEqual(status, 400, f"{path} {payload!r} -> {body!r}")

    def test_stats_taxonomy_mcp_endpoints(self):
        for path, key in (("/api/stats", "active_mcp_tools"), ("/api/taxonomy", "categories"), ("/api/mcp/tools", "count")):
            status, _, body = self._raw_request("GET", path)
            self.assertEqual(status, 200)
            data = json.loads(body.decode())
            self.assertIn(key, data)

    def test_post_audit_endpoint(self):
        payload = json.dumps({
            "title": "Botanical Wildflower Heavy Blend Crewneck Sweatshirt, Cottagecore Floral Gift, Garment Dyed Pullover",
            "tags": [
                "wildflower crewneck", "botanical sweatshirt", "cottagecore gift",
                "floral pullover", "garden lover gift", "nature crewneck",
                "cozy floral shirt", "spring botanical", "pressed flower art",
                "embroidered look", "comfort colors 1717", "gift for gardener",
                "aesthetic sweater",
            ],
            "description": "Heavyweight unisex crewneck sweatshirt printed with archival botanical artwork. Sizing chart and cold-wash care included.",
        }).encode()
        status, _, body = self._raw_request("POST", "/api/audit", body=payload, headers={"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        data = json.loads(body.decode())
        self.assertEqual(data["grade"], "A+")
        self.assertTrue(data["is_ready_to_publish"])

    def test_post_profit_12_and_15_offsite_ads_and_rounding(self):
        # Verify gross_revenue rounding (38.99 + 4.99 == 43.98, not 43.980000000000004)
        for rate, expected_tier in ((0.0, "0% (Organic)"), (0.12, "12% (>=$10k/yr)"), (0.15, "15% (<$10k/yr)")):
            payload = json.dumps({
                "retail_price": 38.99,
                "pod_base_cost": 15.50,
                "shipping_charged": 4.99,
                "offsite_ads_rate": rate,
            }).encode()
            status, _, body = self._raw_request("POST", "/api/profit", body=payload, headers={"Content-Type": "application/json"})
            self.assertEqual(status, 200)
            data = json.loads(body.decode())
            self.assertEqual(data["gross_revenue"], 43.98)
            self.assertEqual(data["offsite_ads_tier"], expected_tier)
            self.assertGreater(data["break_even_price"], 0)

        p12 = calculate_profit(38.99, 15.50, offsite_ads_rate=0.12)
        p15 = calculate_profit(38.99, 15.50, offsite_ads_rate=0.15)
        self.assertAlmostEqual(p12["etsy_fees"]["offsite_ads_fee"], round(38.99 * 0.12, 2))
        self.assertAlmostEqual(p15["etsy_fees"]["offsite_ads_fee"], round(38.99 * 0.15, 2))
        self.assertGreater(p12["net_profit"], p15["net_profit"])

    def test_post_pod_printify_and_gelato(self):
        p_payload = json.dumps({
            "provider": "printify",
            "blueprint_key": "ceramic_mug_15oz",
            "title": "Songbird 15oz Mug",
            "tags": ["songbird mug"],
            "design_image_url": "https://example.com/art.png",
        }).encode()
        status, _, body = self._raw_request("POST", "/api/pod", body=p_payload, headers={"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        pdata = json.loads(body.decode())
        self.assertEqual(pdata["provider"], "printify")
        self.assertEqual(pdata["print_provider_id"], 26)
        self.assertNotIn("target_demographic", pdata["metadata"])

        g_payload = json.dumps({
            "provider": "gelato",
            "blueprint_key": "fine_art_poster_18x24",
            "title": "Botanical Archival Poster 18x24",
            "tags": ["botanical poster"],
            "design_image_url": "https://example.com/poster.png",
        }).encode()
        status, _, body = self._raw_request("POST", "/api/pod", body=g_payload, headers={"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        gdata = json.loads(body.decode())
        self.assertEqual(gdata["provider"], "gelato")
        self.assertEqual(gdata["apiVersion"], "v4")
        self.assertIn("productUid", gdata["variants"][0])

    def test_upload_listing_image_live_dry_run_and_mime(self):
        live = EtsyClient(api_key="test_key", access_token="test_tok", shop_id="shop_1", simulate=False)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            res = live.upload_listing_image("12345", tmp.name, rank=1, confirm=False)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["status"], "not_sent")
        self.assertEqual(res["mime_type"], "image/jpeg")

    def test_post_create_draft_endpoint(self):
        payload = json.dumps({
            "title": "Botanical Geometric Fleece Blanket",
            "description": "Soft archival print throw blanket.",
            "price": 42.50,
            "quantity": 50,
            "tags": ["geometric blanket", "fleece throw", "botanical decor"],
        }).encode()
        status, _, body = self._raw_request("POST", "/api/create-draft", body=payload, headers={"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        data = json.loads(body.decode())
        self.assertEqual(data["status"], "draft")
        self.assertIn("listing_id", data)


if __name__ == "__main__":
    unittest.main()
