"""Test suite for EtsyMcpServer JSON-RPC 2.0 protocol."""

from __future__ import annotations

import json
import unittest
from etsy_connector.mcp_server import EtsyMcpServer, MCP_TOOLS_DEFINITIONS


class TestEtsyMcpServer(unittest.TestCase):
    def setUp(self):
        self.server = EtsyMcpServer()

    def test_tools_definitions_count(self):
        self.assertEqual(len(MCP_TOOLS_DEFINITIONS), 8)
        tool_names = [t["name"] for t in MCP_TOOLS_DEFINITIONS]
        self.assertIn("etsy_search_listings", tool_names)
        self.assertIn("etsy_audit_listing_seo", tool_names)
        self.assertIn("etsy_calculate_profit_margins", tool_names)
        self.assertIn("etsy_get_taxonomy_categories", tool_names)
        self.assertIn("etsy_create_draft_listing", tool_names)
        self.assertIn("etsy_upload_listing_image", tool_names)
        self.assertIn("etsy_get_shop_details", tool_names)
        self.assertIn("etsy_generate_pod_payload", tool_names)

    def test_mcp_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "etsy-connector")

    def test_mcp_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = self.server.handle_request(req)
        self.assertEqual(len(resp["result"]["tools"]), 8)

    def test_mcp_call_search(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "etsy_search_listings",
                "arguments": {"keywords": "wildflower mug", "limit": 3},
            },
        }
        resp = self.server.handle_request(req)
        self.assertFalse(resp["result"]["isError"])
        content = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(content["simulation"])
        self.assertTrue(len(content["results"]) > 0)

    def test_mcp_call_audit_seo(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "etsy_audit_listing_seo",
                "arguments": {
                    "title": "Grandma's Garden Wildflower Sweatshirt, Cozy Cottagecore Gift, Floral Crewneck",
                    "tags": [
                        "grandma sweatshirt", "garden crewneck", "cottagecore gift",
                        "wildflower shirt", "mothers day gift", "comfort colors 1717",
                        "plant lover gift", "floral sweater", "grandparent gift",
                        "gardening era", "botanical pullover", "watercolor flower",
                        "cozy grandma gift"
                    ],
                },
            },
        }
        resp = self.server.handle_request(req)
        self.assertFalse(resp["result"]["isError"])
        content = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(content["grade"], "A+")
        self.assertTrue(content["is_ready_to_publish"])

    def test_mcp_call_profit(self):
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "etsy_calculate_profit_margins",
                "arguments": {"retail_price": 24.99, "pod_base_cost": 7.20},
            },
        }
        resp = self.server.handle_request(req)
        self.assertFalse(resp["result"]["isError"])
        content = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(content["net_profit"] > 14.0)

    def test_mcp_call_taxonomy(self):
        req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "etsy_get_taxonomy_categories",
                "arguments": {"query": "sweatshirt"},
            },
        }
        resp = self.server.handle_request(req)
        self.assertFalse(resp["result"]["isError"])
        content = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(content["result"]["id"], 1099)


if __name__ == "__main__":
    unittest.main()
