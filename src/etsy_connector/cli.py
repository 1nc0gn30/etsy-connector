"""Command Line Interface for Etsy Connector.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .client import EtsyClient
from .mcp_server import EtsyMcpServer
from .seo_engine import audit_listing, calculate_profit
from .web_cockpit import run_server


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="etsy-connector",
        description="Etsy Open API v3 & Print-on-Demand Connector for Antigravity & Sovereign AI Agents.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: mcp
    mcp_p = subparsers.add_parser("mcp", help="Run JSON-RPC 2.0 stdio MCP server for Antigravity")

    # Command: serve
    serve_p = subparsers.add_parser("serve", help="Run REST API and Glassmorphic Web Cockpit")
    serve_p.add_argument("--port", type=int, default=8108, help="Port to bind server (default: 8108)")
    serve_p.add_argument("--host", default=None, help="Host interface (default: 127.0.0.1 or $ZOTH_BIND_HOST; use 0.0.0.0 only on trusted networks)")

    # Command: audit
    audit_p = subparsers.add_parser("audit", help="Audit Etsy listing title and 13 tags for SEO ranking")
    audit_p.add_argument("--title", required=True, help="Listing title")
    audit_p.add_argument("--tags", required=True, help="Comma-separated list of search tags")
    audit_p.add_argument("--desc", default="", help="Optional description text")
    audit_p.add_argument("--json", action="store_true", help="Output audit report as JSON")

    # Command: profit
    profit_p = subparsers.add_parser("profit", help="Calculate Etsy fees, POD production costs, and net margins")
    profit_p.add_argument("--retail", type=float, required=True, help="Retail price in USD")
    profit_p.add_argument("--pod", type=float, required=True, help="POD production base cost in USD")
    profit_p.add_argument("--shipping", type=float, default=0.0, help="Shipping charged to customer")
    profit_p.add_argument("--ads", action="store_true", help="Include 15%% Etsy offsite ads fee")
    profit_p.add_argument("--json", action="store_true", help="Output profit report as JSON")

    # Command: search
    search_p = subparsers.add_parser("search", help="Search active Etsy listings for competitor intelligence")
    search_p.add_argument("--keywords", required=True, help="Search keywords")
    search_p.add_argument("--limit", type=int, default=10, help="Max results to return (default: 10)")
    search_p.add_argument("--json", action="store_true", help="Output search results as JSON")

    # Command: config
    cfg_p = subparsers.add_parser("config", help="Save live Etsy API v3 credentials to ~/.etsy_connector_config.json")
    cfg_p.add_argument("--key", required=True, help="Etsy API Keystring (Client ID)")
    cfg_p.add_argument("--token", default="", help="OAuth 2.0 Bearer Access Token")
    cfg_p.add_argument("--shop", default="metadigitalgoods", help="Shop ID or Shop Name (default: metadigitalgoods)")

    # Command: auth
    auth_p = subparsers.add_parser("auth", help="Generate OAuth 2.0 PKCE authorization link or exchange code for Etsy Open API v3")
    auth_p.add_argument("--key", default="", help="Etsy API Keystring (or Keystring:SharedSecret)")
    auth_p.add_argument("--redirect", default="https://metadigitalgoods.nealfrazier.tech/oauth/callback/", help="Redirect URI")
    auth_p.add_argument("--exchange-code", default="", help="Exchange returned OAuth authorization code for an access token")

    # Command: shop-update
    shop_p = subparsers.add_parser("shop-update", help="Update shop title, announcement, and buyer messages via API")
    shop_p.add_argument("--title", default=None, help="Shop tagline/title (max 140 chars)")
    shop_p.add_argument("--announcement", default=None, help="Shop announcement text")
    shop_p.add_argument("--digital-msg", default=None, help="Automatic message sent to digital download buyers")
    shop_p.add_argument("--confirm", action="store_true", help="Execute live PUT against Etsy API")

    # Command: draft-digital
    draft_p = subparsers.add_parser("draft-digital", help="Create a digital download draft listing + attach files/mockups")
    draft_p.add_argument("--title", required=True, help="Listing title (max 140 chars)")
    draft_p.add_argument("--desc", required=True, help="Listing description")
    draft_p.add_argument("--price", type=float, required=True, help="Retail price in USD (e.g. 6.99)")
    draft_p.add_argument("--tags", required=True, help="Comma-separated 13 search tags (each <= 20 chars)")
    draft_p.add_argument("--file", default=None, help="Optional path to digital PDF/ZIP file to attach")
    draft_p.add_argument("--image", default=None, help="Optional path to listing mockup image (PNG/JPG)")
    draft_p.add_argument("--confirm", action="store_true", help="Execute live POST against Etsy API")

    args = parser.parse_args(argv)
    cmd = args.command or "serve"

    if cmd == "mcp":
        server = EtsyMcpServer()
        server.run_stdio()
        return 0

    elif cmd == "serve":
        run_server(port=args.port, host=args.host)
        return 0

    elif cmd == "config":
        client = EtsyClient()
        client.save_credentials(api_key=args.key, access_token=args.token, shop_id=args.shop)
        print(f"✅ Saved Etsy credentials for shop '{args.shop}' to ~/.etsy_connector_config.json (0600 permissions).")
        return 0

    elif cmd == "auth":
        client = EtsyClient()
        if args.exchange_code:
            token_data = client.exchange_oauth_code(args.exchange_code)
            print("✅ OAuth 2.0 Access Token acquired and saved to ~/.etsy_connector_config.json!")
            print(json.dumps(token_data, indent=2))
            return 0
        key_to_use = args.key or client.api_key
        if not key_to_use:
            raise ValueError("Please provide --key <KEYSTRING>.")
        pkce = EtsyClient.generate_oauth_pkce(api_key=key_to_use, redirect_uri=args.redirect)
        print("\n🔐 Etsy Open API v3 OAuth 2.0 PKCE Flow:")
        print(f"1. Open this URL in your browser to authorize MetaDigitalGoods:\n   {pkce['auth_url']}\n")
        print(f"2. Code Verifier (auto-saved to config):    {pkce['code_verifier']}")
        print(f"3. State:                                   {pkce['state']}\n")
        return 0

    elif cmd == "shop-update":
        client = EtsyClient()
        res = client.update_shop(
            title=args.title,
            announcement=args.announcement,
            digital_sale_message=args.digital_msg,
            confirm=args.confirm,
        )
        print(json.dumps(res, indent=2))
        return 0

    elif cmd == "draft-digital":
        client = EtsyClient()
        tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        res = client.create_draft_listing(
            title=args.title,
            description=args.desc,
            price=args.price,
            tags=tag_list,
            listing_type="download",
            confirm=args.confirm,
        )
        listing_id = str(res.get("listing_id", "sim_listing"))
        if args.image:
            res["image_upload"] = client.upload_listing_image(listing_id=listing_id, image_path=args.image)
        if args.file:
            res["file_upload"] = client.upload_listing_file(listing_id=listing_id, file_path=args.file)
        print(json.dumps(res, indent=2))
        return 0

    elif cmd == "audit":
        tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        report = audit_listing(title=args.title, tags=tag_list, description=args.desc)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"\n⚡ Etsy SEO Audit: {report['grade']} ({report['overall_score']}/100)")
            print(f"Title: {report['title_audit']['char_length']}/140 chars (Valid: {report['title_audit']['valid']})")
            print(f"Tags:  {report['tags_audit']['tag_count']}/13 tags (Valid: {report['tags_audit']['valid']})")
            if report['title_audit']['issues']:
                print("\nTitle Issues:")
                for i in report['title_audit']['issues']:
                    print(f"  • {i}")
            if report['tags_audit']['issues']:
                print("\nTag Issues:")
                for i in report['tags_audit']['issues']:
                    print(f"  • {i}")
            print(f"\nReady to Publish: {report['is_ready_to_publish']}\n")
        return 0 if report["is_ready_to_publish"] else 1

    elif cmd == "profit":
        res = calculate_profit(
            retail_price=args.retail,
            pod_base_cost=args.pod,
            shipping_charged=args.shipping,
            is_offsite_ads=args.ads,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"\n💰 Profit & Margin Analysis:")
            print(f"Retail Price:      ${res['retail_price']:.2f}")
            print(f"POD Base Cost:     ${res['pod_base_cost']:.2f}")
            print(f"Total Etsy Fees:   ${res['etsy_fees']['total_etsy_fees']:.2f}")
            print(f"Total Costs:       ${res['total_costs']:.2f}")
            print(f"Net Profit:        ${res['net_profit']:.2f} ({res['net_margin_pct']}% margin)")
            print(f"ROI:               {res['roi_pct']}%\n")
        return 0

    elif cmd == "search":
        client = EtsyClient()
        res = client.search_listings(keywords=args.keywords, limit=args.limit)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"\n🔍 Etsy Search: '{args.keywords}' ({res.get('count', 0)} results)")
            for item in res.get("results", []):
                p = item.get("price", {})
                price_str = f"${p.get('amount', 0) / p.get('divisor', 100):.2f}"
                print(f"  • [{price_str}] {item.get('title', '')[:70]}... (Shop: {item.get('shop_name')})")
            print()
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

