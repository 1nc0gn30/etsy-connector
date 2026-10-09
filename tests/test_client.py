"""Test suite for EtsyClient."""

from __future__ import annotations

import unittest
from etsy_connector.client import EtsyClient


class TestEtsyClient(unittest.TestCase):
    def setUp(self):
        # Simulation client with zero external dependencies
        self.client = EtsyClient(simulate=True)

    def test_simulation_mode_active(self):
        self.assertTrue(self.client.simulate)

    def test_search_listings(self):
        res = self.client.search_listings(keywords="wildflower sweatshirt", limit=5)
        self.assertTrue(res.get("simulation"))
        self.assertTrue(len(res.get("results", [])) > 0)
        first = res["results"][0]
        self.assertIn("title", first)
        self.assertIn("price", first)
        self.assertIn("tags", first)

    def test_get_shop(self):
        res = self.client.get_shop()
        self.assertTrue(res.get("simulation"))
        self.assertIn("shop_name", res)
        self.assertIn("review_average", res)

    def test_create_draft_listing(self):
        res = self.client.create_draft_listing(
            title="Grandma Garden Floral Sweatshirt",
            description="Cozy floral crewneck",
            price=34.99,
            tags=["grandma gift", "floral sweater"],
            taxonomy_id=1099,
        )
        self.assertTrue(res.get("simulation"))
        self.assertEqual(res.get("status"), "draft")
        self.assertIn("listing_id", res)
        self.assertEqual(res.get("price", {}).get("amount"), 3499)

    def test_upload_listing_image(self):
        res = self.client.upload_listing_image(listing_id="1782349011", image_path="/tmp/mockup.png", rank=1)
        self.assertTrue(res.get("simulation"))
        self.assertEqual(res.get("status"), "uploaded")
        self.assertIn("image_id", res)


if __name__ == "__main__":
    unittest.main()
