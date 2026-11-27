"""Command Line Interface for Etsy Connector.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.request
import webbrowser
from typing import Any, Dict, List, Optional

from . import __version__
from .client import DEFAULT_REDIRECT_URI, EtsyClient
from .mcp_server import EtsyMcpServer, MCP_TOOLS_DEFINITIONS
from .pod_bridge import generate_pod_payload, get_all_provider_catalogs
from .seo_engine import audit_listing, calculate_profit
from .web_cockpit import run_server


def _probe_local_server(port: int = 8108) -> Dict[str, Any]:
    """Check whether the local loopback cockpit is running."""
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=0.6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"running": True, "url": f"http://127.0.0.1:{port}", "health": data}
    except Exception:
        return {"running": False, "url": f"http://127.0.0.1:{port}", "health": None}


def _collect_status(port: int = 8108) -> Dict[str, Any]:
    client = EtsyClient()
    probe = _probe_local_server(port)
    catalogs = get_all_provider_catalogs()
    return {
        "tool": "etsy-connector",
        "version": __version__,
        "ok": True,
        "local_port": port,
        "local_url": f"http://127.0.0.1:{port}",
        "studio_route": "/tools/etsy-connector",
        "daemon_running": probe["running"],
        "is_configured": client.is_configured(),
        "simulation_mode": client.simulate,
        "mcp_tool_count": len(MCP_TOOLS_DEFINITIONS),
        "pod_providers": {
            "printify_blueprints": len(catalogs["printify"]),
            "gelato_products": len(catalogs["gelato"]),
        },
        "health": probe["health"],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="etsy-connector",
        description=f"Etsy Open API v3, 13-Tag SEO Auditor, Fee Engine & Printify/Gelato POD Connector (v{__version__}).",
    )
    parser.add_argument("--version", action="version", version=f"etsy-connector {__version__}")
    parser.add_argument("--status", action="store_true", help="Print local daemon, credential, and MCP status")
    parser.add_argument("--json", action="store_true", help="Output structured JSON where applicable")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: mcp
    subparsers.add_parser("mcp", help="Run JSON-RPC 2.0 stdio MCP server for Antigravity")

    # Command: serve
    serve_p = subparsers.add_parser("serve", help="Run REST API and Dual-Theme Web Cockpit")
    serve_p.add_argument("--port", type=int, default=8108, help="Port to bind server (default: 8108)")
    serve_p.add_argument("--host", default=None, help="Host interface (default: 127.0.0.1 or $ZOTH_BIND_HOST)")

    # Command: status
    status_p = subparsers.add_parser("status", help="Show local daemon, API, and MCP bridge status")
    status_p.add_argument("--port", type=int, default=8108, help="Loopback port to inspect (default: 8108)")
    status_p.add_argument("--json", action="store_true", help="Output status as JSON")

    # Command: desktop
    desktop_p = subparsers.add_parser("desktop", help="Open the Etsy Connector local workstation in a browser")
    desktop_p.add_argument("--port", type=int, default=8108, help="Loopback port (default: 8108)")
    desktop_p.add_argument("--no-browser", action="store_true", help="Print target URL without opening a browser")

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
    profit_p.add_argument("--shipping-cost", type=float, default=0.0, help="Outbound shipping cost paid by merchant")
    profit_p.add_argument("--ads", action="store_true", help="Include 15%% Etsy Offsite Ads fee")
    profit_p.add_argument(
        "--offsite-ads-rate",
        type=float,
        default=None,
        help="Explicit Offsite Ads rate (0, 0.12 for >=$10k/yr shops, or 0.15 for <$10k/yr shops)",
    )
    profit_p.add_argument("--json", action="store_true", help="Output profit report as JSON")

    # Command: pod
    pod_p = subparsers.add_parser("pod", help="Generate Printify or Gelato POD fulfillment payload")
    pod_p.add_argument("--provider", choices=["printify", "gelato"], default="printify", help="Fulfillment provider")
    pod_p.add_argument("--blueprint", default="comfort_colors_1717", help="Blueprint key")
    pod_p.add_argument("--title", required=True, help="Product title")
    pod_p.add_argument("--desc", default="", help="Product description")
    pod_p.add_argument("--tags", default="", help="Comma-separated search tags")
    pod_p.add_argument("--image", default="https://assets.nullai.tech/sample_wildflower.png", help="300 DPI design URL")
    pod_p.add_argument("--price", type=float, default=None, help="Optional retail price override in USD")
    pod_p.add_argument("--json", action="store_true", help="Output payload as JSON")

    # Command: search
    search_p = subparsers.add_parser("search", help="Search active Etsy listings for competitor intelligence")
    search_p.add_argument("--keywords", required=True, help="Search keywords")
    search_p.add_argument("--limit", type=int, default=10, help="Max results to return (default: 10)")
    search_p.add_argument("--json", action="store_true", help="Output search results as JSON")

    # Command: config
    cfg_p = subparsers.add_parser("config", help="Save live Etsy API v3 credentials to ~/.etsy_connector_config.json")
    cfg_p.add_argument("--key", required=True, help="Etsy API Keystring (Client ID)")
    cfg_p.add_argument("--token", default="", help="OAuth 2.0 Bearer Access Token")
    cfg_p.add_argument("--shop", default=os.environ.get("ETSY_SHOP_ID", "me"), help="Shop ID or Shop Name (default: me)")

    # Command: auth
    auth_p = subparsers.add_parser("auth", help="Generate OAuth 2.0 PKCE authorization link or exchange code for Etsy Open API v3")
    auth_p.add_argument("--key", default="", help="Etsy API Keystring (or Keystring:SharedSecret)")
    auth_p.add_argument(
        "--redirect",
        default=os.environ.get("ETSY_REDIRECT_URI", DEFAULT_REDIRECT_URI),
        help=f"Redirect URI (default: {DEFAULT_REDIRECT_URI})",
    )
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

    if args.status or args.command == "status":
        port = getattr(args, "port", 8108)
        st = _collect_status(port=port)
        if args.json:
            print(json.dumps(st, indent=2, sort_keys=True))
        else:
            state = "ONLINE" if st["daemon_running"] else "IDLE (on-demand)"
            mode = "LIVE" if st["is_configured"] else "SIMULATION"
            print(f"etsy-connector v{__version__} · {state} · http://127.0.0.1:{port} · mode={mode} · mcp_tools={st['mcp_tool_count']}")
        return 0

    cmd = args.command or "serve"

    if cmd == "mcp":
        server = EtsyMcpServer()
        server.run_stdio()
        return 0

    elif cmd == "serve":
        run_server(port=args.port, host=args.host)
        return 0

    elif cmd == "desktop":
        port = args.port
        probe = _probe_local_server(port)
        url = f"http://127.0.0.1:{port}/" if probe["running"] else "http://127.0.0.1:3000/tools/etsy-connector"
        if not args.no_browser and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            try:
                webbrowser.open(url)
            except Exception:
                pass
        print(json.dumps({"ok": True, "action": "desktop", "url": url, "daemon_running": probe["running"]}))
        return 0

    elif cmd == "config":
        client = EtsyClient()
        client.save_credentials(api_key=args.key, access_token=args.token, shop_id=args.shop)
        print(f"Saved Etsy credentials for shop '{args.shop}' to ~/.etsy_connector_config.json (0600 permissions).")
        return 0

    elif cmd == "auth":
        client = EtsyClient()
        if args.exchange_code:
            token_data = client.exchange_oauth_code(args.exchange_code)
            print("OAuth 2.0 Access Token acquired and saved to ~/.etsy_connector_config.json.")
            print(json.dumps(token_data, indent=2))
            return 0
        key_to_use = args.key or client.api_key
        if not key_to_use:
            raise ValueError("Please provide --key <KEYSTRING>.")
        pkce = EtsyClient.generate_oauth_pkce(api_key=key_to_use, redirect_uri=args.redirect)
        print("\nEtsy Open API v3 OAuth 2.0 PKCE Flow:")
        print(f"1. Open this URL in your browser to authorize your Etsy shop:\n   {pkce['auth_url']}\n")
        print(f"2. Code Verifier (saved to ~/.etsy_connector_config.json): {pkce['code_verifier']}")
        print(f"3. State: {pkce['state']}\n")
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
            res["image_upload"] = client.upload_listing_image(
                listing_id=listing_id,
                image_path=args.image,
                confirm=args.confirm,
            )
        if args.file:
            res["file_upload"] = client.upload_listing_file(
                listing_id=listing_id,
                file_path=args.file,
                confirm=args.confirm,
            )
        print(json.dumps(res, indent=2))
        return 0

    elif cmd == "audit":
        tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        report = audit_listing(title=args.title, tags=tag_list, description=args.desc)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"\nEtsy SEO Audit: {report['grade']} ({report['overall_score']}/100)")
            print(f"Title: {report['title_audit']['char_length']}/140 chars (Valid: {report['title_audit']['valid']})")
            print(f"Tags:  {report['tags_audit']['tag_count']}/13 tags (Valid: {report['tags_audit']['valid']})")
            if report["title_audit"]["issues"]:
                print("\nTitle Issues:")
                for i in report["title_audit"]["issues"]:
                    print(f"  - {i}")
            if report["tags_audit"]["issues"]:
                print("\nTag Issues:")
                for i in report["tags_audit"]["issues"]:
                    print(f"  - {i}")
            print(f"\nReady to Publish: {report['is_ready_to_publish']}\n")
        return 0 if report["is_ready_to_publish"] else 1

    elif cmd == "profit":
        res = calculate_profit(
            retail_price=args.retail,
            pod_base_cost=args.pod,
            shipping_charged=args.shipping,
            shipping_cost=args.shipping_cost,
            is_offsite_ads=args.ads,
            offsite_ads_rate=args.offsite_ads_rate,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("\nProfit & Margin Analysis:")
            print(f"Gross Revenue:     ${res['gross_revenue']:.2f}")
            print(f"POD Base Cost:     ${res['pod_base_cost']:.2f}")
            print(f"Offsite Ads Tier:  {res['offsite_ads_tier']}")
            print(f"Total Etsy Fees:   ${res['etsy_fees']['total_etsy_fees']:.2f}")
            print(f"Total Costs:       ${res['total_costs']:.2f}")
            print(f"Net Profit:        ${res['net_profit']:.2f} ({res['net_margin_pct']}% margin)")
            print(f"Break-Even Retail: ${res['break_even_price']:.2f}")
            print(f"ROI:               {res['roi_pct']}%\n")
        return 0

    elif cmd == "pod":
        tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        payload = generate_pod_payload(
            blueprint_key=args.blueprint,
            title=args.title,
            description=args.desc,
            tags=tag_list,
            design_image_url=args.image,
            retail_price_usd=args.price,
            provider=args.provider,
        )
        print(json.dumps(payload, indent=2))
        return 0

    elif cmd == "search":
        client = EtsyClient()
        res = client.search_listings(keywords=args.keywords, limit=args.limit)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"\nEtsy Search: '{args.keywords}' ({res.get('count', 0)} results)")
            for item in res.get("results", []):
                p = item.get("price", {})
                price_str = f"${p.get('amount', 0) / p.get('divisor', 100):.2f}"
                print(f"  - [{price_str}] {item.get('title', '')[:70]}... (Shop: {item.get('shop_name')})")
            print()
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
