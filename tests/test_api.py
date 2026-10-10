"""Test suite for etsy-connector REST API endpoints."""

from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from etsy_connector.client import EtsyClient
from etsy_connector.web_cockpit import EtsyCockpitHandler

TEST_PORT = 18107


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
        cls.server = ThreadingHTTPServer(("127.0.0.1", TEST_PORT), EtsyCockpitHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_health_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/health"
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["service"], "etsy-connector")
            self.assertEqual(data["port"], 8108)

    def test_stats_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/stats"
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertIn("active_mcp_tools", data)
            self.assertEqual(data["active_mcp_tools"], 8)

    def test_taxonomy_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/taxonomy"
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(len(data.get("categories", [])) >= 6)

    def test_mcp_tools_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/mcp/tools"
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["count"], 8)

    def test_post_audit_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/audit"
        payload = json.dumps({
            "title": "Grandma's Garden Wildflower Sweatshirt, Cozy Cottagecore Gift, Floral Crewneck",
            "tags": [
                "grandma sweatshirt", "garden crewneck", "cottagecore gift",
                "wildflower shirt", "mothers day gift", "comfort colors 1717",
                "plant lover gift", "floral sweater", "grandparent gift",
                "gardening era", "botanical pullover", "watercolor flower",
                "cozy grandma gift"
            ],
            "description": "Premium fleece crewneck.",
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["grade"], "A+")
            self.assertTrue(data["is_ready_to_publish"])

    def test_post_profit_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/profit"
        payload = json.dumps({"retail_price": 34.99, "pod_base_cost": 12.80}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(data["net_profit"] > 17.0)


if __name__ == "__main__":
    unittest.main()
