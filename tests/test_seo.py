"""Test suite for SEO Engine and Profit Calculator."""

from __future__ import annotations

import unittest
from etsy_connector.seo_engine import audit_listing, audit_tags, audit_title, calculate_profit


class TestSeoEngine(unittest.TestCase):
    def test_audit_title_valid(self):
        title = "Grandma's Garden Wildflower Sweatshirt, Cozy Cottagecore Gift, Floral Crewneck"
        res = audit_title(title)
        self.assertTrue(res["valid"])
        self.assertTrue(res["score"] >= 90)
        self.assertEqual(res["char_length"], len(title))

    def test_audit_title_too_long(self):
        long_title = "A" * 150
        res = audit_title(long_title)
        self.assertFalse(res["valid"])
        self.assertTrue(res["score"] < 70)
        self.assertTrue(any("exceeds" in issue.lower() for issue in res["issues"]))

    def test_audit_tags_valid_13(self):
        tags = [
            "grandma sweatshirt", "garden crewneck", "cottagecore gift",
            "wildflower shirt", "mothers day gift", "comfort colors 1717",
            "plant lover gift", "floral sweater", "grandparent gift",
            "gardening era", "botanical pullover", "watercolor flower",
            "cozy grandma gift"
        ]
        res = audit_tags(tags)
        self.assertTrue(res["valid"])
        self.assertEqual(res["tag_count"], 13)
        self.assertEqual(len(res["invalid_tags"]), 0)
        self.assertEqual(res["score"], 100)

    def test_audit_tags_over_20_chars(self):
        tags = ["this tag is way too long over 20 chars", "valid tag"]
        res = audit_tags(tags)
        self.assertFalse(res["valid"])
        self.assertEqual(len(res["invalid_tags"]), 1)

    def test_audit_listing_full(self):
        title = "Grandma's Garden Wildflower Sweatshirt, Cozy Cottagecore Gift, Floral Crewneck"
        tags = [
            "grandma sweatshirt", "garden crewneck", "cottagecore gift",
            "wildflower shirt", "mothers day gift", "comfort colors 1717",
            "plant lover gift", "floral sweater", "grandparent gift",
            "gardening era", "botanical pullover", "watercolor flower",
            "cozy grandma gift"
        ]
        desc = "Cozy garment-dyed crewneck sweatshirt perfect for grandmas, moms, and garden lovers. Crafted with premium soft fleece."
        res = audit_listing(title, tags, desc)
        self.assertTrue(res["is_ready_to_publish"])
        self.assertIn(res["grade"], ["A+", "A"])
        self.assertTrue(res["overall_score"] >= 90)

    def test_profit_calculator(self):
        # Gildan 18000 sweatshirt: $38.99 retail, $15.50 POD cost
        res = calculate_profit(retail_price=38.99, pod_base_cost=15.50)
        self.assertTrue(res["profitable"])
        self.assertAlmostEqual(res["retail_price"], 38.99)
        self.assertAlmostEqual(res["pod_base_cost"], 15.50)
        self.assertTrue(res["net_profit"] > 18.00)
        self.assertTrue(res["net_margin_pct"] > 45.0)
        self.assertEqual(res["etsy_fees"]["listing_fee"], 0.20)


if __name__ == "__main__":
    unittest.main()
