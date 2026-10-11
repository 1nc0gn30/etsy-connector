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

    args = parser.parse_args(argv)
    cmd = args.command or "serve"

    if cmd == "mcp":
        server = EtsyMcpServer()
        server.run_stdio()
        return 0

    elif cmd == "serve":
        run_server(port=args.port, host=args.host)
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
