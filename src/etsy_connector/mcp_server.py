"""Model Context Protocol (MCP) Server for Etsy Connector.

Exposes Etsy operations, SEO audits, and Print-on-Demand bridges directly
to Antigravity AI agents via standard JSON-RPC 2.0 over stdio.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import EtsyClient
from .pod_bridge import generate_printify_product_payload, get_available_blueprints
from .seo_engine import audit_listing, audit_tags, audit_title, calculate_profit
from .taxonomy import find_taxonomy, get_taxonomy_categories

SERVER_NAME = "etsy-connector"
SERVER_VERSION = "0.1.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

MCP_TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "etsy_search_listings",
        "description": "Search active Etsy marketplace listings for competitor research, pricing analysis, and popular keywords.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Keywords to search on Etsy (e.g. 'grandma garden sweatshirt' or 'wildflower mug').",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of listings to return (default: 10, max: 50).",
                    "default": 10,
                },
                "min_price": {
                    "type": "number",
                    "description": "Optional minimum price filter in USD.",
                },
                "max_price": {
                    "type": "number",
                    "description": "Optional maximum price filter in USD.",
                },
            },
            "required": ["keywords"],
        },
    },
    {
        "name": "etsy_audit_listing_seo",
        "description": "Audit an Etsy listing's title, 13 tags, and description against Etsy search algorithm ranking factors and character constraints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Listing title (max 140 chars).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of 13 search tags (each tag strictly <= 20 chars).",
                },
                "description": {
                    "type": "string",
                    "description": "Optional listing body description.",
                    "default": "",
                },
            },
            "required": ["title", "tags"],
        },
    },
    {
        "name": "etsy_calculate_profit_margins",
        "description": "Calculate exact Etsy fees (listing, transaction, payment processing, offsite ads), POD production costs, net profit, and profit margin %.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "retail_price": {
                    "type": "number",
                    "description": "Item retail selling price in USD.",
                },
                "pod_base_cost": {
                    "type": "number",
                    "description": "Base production cost from POD provider (e.g. $12.80 for Comfort Colors 1717, $6.80 for 15oz mug).",
                },
                "shipping_charged": {
                    "type": "number",
                    "description": "Shipping fee charged to customer (default: 0.0 for free shipping).",
                    "default": 0.0,
                },
                "shipping_cost": {
                    "type": "number",
                    "description": "Actual shipping fulfillment cost charged by POD provider (default: 0.0).",
                    "default": 0.0,
                },
                "is_offsite_ads": {
                    "type": "boolean",
                    "description": "Set to true to calculate 15% Etsy Offsite Ads fee (default: false).",
                    "default": False,
                },
            },
            "required": ["retail_price", "pod_base_cost"],
        },
    },
    {
        "name": "etsy_get_taxonomy_categories",
        "description": "Look up Etsy seller category taxonomy IDs, names, and keyword mappings for POD products (Apparel, Mugs, Totes, Prints, Patterns).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional search term to filter taxonomy (e.g. 'sweatshirt', 'mug', 'wall art').",
                }
            },
        },
    },
    {
        "name": "etsy_create_draft_listing",
        "description": "Create a new draft listing on Etsy with complete title, description, price, 13 tags, and taxonomy ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Listing title (max 140 characters).",
                },
                "description": {
                    "type": "string",
                    "description": "Full product description including materials, sizing, and care.",
                },
                "price": {
                    "type": "number",
                    "description": "Retail price in USD (e.g. 34.99).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of up to 13 search tags (each tag <= 20 chars).",
                },
                "taxonomy_id": {
                    "type": "integer",
                    "description": "Etsy category taxonomy ID (e.g. 1099 for Sweatshirts, 1085 for Mugs).",
                    "default": 1099,
                },
                "quantity": {
                    "type": "integer",
                    "description": "Inventory stock quantity (default: 999 for POD).",
                    "default": 999,
                },
            },
            "required": ["title", "description", "price", "tags"],
        },
    },
    {
        "name": "etsy_upload_listing_image",
        "description": "Upload a mockup image or design file to an Etsy listing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "listing_id": {
                    "type": "string",
                    "description": "Target Etsy listing ID.",
                },
                "image_path": {
                    "type": "string",
                    "description": "Absolute file path to the PNG/JPG mockup image on disk.",
                },
                "rank": {
                    "type": "integer",
                    "description": "Display order rank of the image (1 to 10).",
                    "default": 1,
                },
            },
            "required": ["listing_id", "image_path"],
        },
    },
    {
        "name": "etsy_get_shop_details",
        "description": "Fetch Etsy shop profile, active listing counts, review score, and vacation status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "string",
                    "description": "Optional shop ID or shop name (defaults to configured shop).",
                }
            },
        },
    },
    {
        "name": "etsy_generate_pod_payload",
        "description": "Generate a Printify / Gelato Print-on-Demand product creation payload linked to Etsy for automated fulfillment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "blueprint_key": {
                    "type": "string",
                    "description": "Blueprint identifier ('comfort_colors_1717', 'gildan_18000', 'ceramic_mug_15oz', 'canvas_tote_heavy', 'digital_wall_art_pack').",
                },
                "title": {
                    "type": "string",
                    "description": "Product title.",
                },
                "description": {
                    "type": "string",
                    "description": "Product description.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of 13 search tags.",
                },
                "design_image_url": {
                    "type": "string",
                    "description": "URL or storage URI of the 300 DPI transparent design artwork.",
                },
                "retail_price_usd": {
                    "type": "number",
                    "description": "Optional retail price override in USD.",
                },
            },
            "required": ["blueprint_key", "title", "tags", "design_image_url"],
        },
    },
]


class EtsyMcpServer:
    """Stdio Model Context Protocol (MCP) server for Etsy integration."""

    def __init__(self, client: Optional[EtsyClient] = None) -> None:
        self.client = client or EtsyClient()
        self.name = SERVER_NAME
        self.version = SERVER_VERSION

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Route tool calls to appropriate engine."""
        if name == "etsy_search_listings":
            kw = arguments.get("keywords", "")
            limit = int(arguments.get("limit", 10))
            min_p = arguments.get("min_price")
            max_p = arguments.get("max_price")
            return self.client.search_listings(keywords=kw, limit=limit, min_price=min_p, max_price=max_p)

        elif name == "etsy_audit_listing_seo":
            title = arguments.get("title", "")
            tags = arguments.get("tags", [])
            desc = arguments.get("description", "")
            return audit_listing(title=title, tags=tags, description=desc)

        elif name == "etsy_calculate_profit_margins":
            retail = float(arguments.get("retail_price", 0.0))
            pod = float(arguments.get("pod_base_cost", 0.0))
            ship_chg = float(arguments.get("shipping_charged", 0.0))
            ship_cost = float(arguments.get("shipping_cost", 0.0))
            ads = bool(arguments.get("is_offsite_ads", False))
            return calculate_profit(retail, pod, ship_chg, ship_cost, ads)

        elif name == "etsy_get_taxonomy_categories":
            q = arguments.get("query")
            if q:
                found = find_taxonomy(q)
                return {"query": q, "result": found} if found else {"query": q, "result": None, "categories": get_taxonomy_categories()}
            return {"categories": get_taxonomy_categories()}

        elif name == "etsy_create_draft_listing":
            title = arguments.get("title", "")
            desc = arguments.get("description", "")
            price = float(arguments.get("price", 29.99))
            qty = int(arguments.get("quantity", 999))
            tags = arguments.get("tags", [])
            tax_id = int(arguments.get("taxonomy_id", 1099))
            return self.client.create_draft_listing(
                title=title,
                description=desc,
                price=price,
                quantity=qty,
                tags=tags,
                taxonomy_id=tax_id,
            )

        elif name == "etsy_upload_listing_image":
            lid = str(arguments.get("listing_id", ""))
            ipath = str(arguments.get("image_path", ""))
            rank = int(arguments.get("rank", 1))
            return self.client.upload_listing_image(listing_id=lid, image_path=ipath, rank=rank)

        elif name == "etsy_get_shop_details":
            sid = arguments.get("shop_id")
            return self.client.get_shop(shop_id=sid)

        elif name == "etsy_generate_pod_payload":
            bp = arguments.get("blueprint_key", "comfort_colors_1717")
            title = arguments.get("title", "")
            desc = arguments.get("description", "")
            tags = arguments.get("tags", [])
            img = arguments.get("design_image_url", "")
            price = arguments.get("retail_price_usd")
            return generate_printify_product_payload(
                blueprint_key=bp,
                title=title,
                description=desc,
                tags=tags,
                design_image_url=img,
                retail_price_usd=price,
            )

        raise KeyError(f"Unknown MCP tool: '{name}'")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if not method:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32600, "message": "Missing 'method'"}}

        if method in ("notifications/initialized", "initialized"):
            return None

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.name, "version": self.version},
                },
            }

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS_DEFINITIONS}}

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result = self.execute_tool(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                        "isError": False,
                    },
                }
            except KeyError as e:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": str(e)}}
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error executing tool '{tool_name}': {str(e)}"}],
                        "isError": True,
                    },
                }

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: '{method}'"}}

    def run_stdio(self) -> None:
        """Run stdio loop reading JSON-RPC lines from stdin and replying to stdout."""
        sys.stderr.write(f"[{SERVER_NAME}] MCP stdio server active (v{SERVER_VERSION}, Python {platform.python_version()})\n")
        sys.stderr.flush()

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line_stripped = line.strip()
                if not line_stripped:
                    continue

                if line_stripped.startswith("Content-Length:"):
                    length = int(line_stripped.split(":")[1].strip())
                    while True:
                        header_line = sys.stdin.readline().strip()
                        if not header_line:
                            break
                    raw_payload = sys.stdin.read(length)
                    data = json.loads(raw_payload)
                else:
                    data = json.loads(line_stripped)

                resp = self.handle_request(data)
                if resp is not None:
                    sys.stdout.write(f"{json.dumps(resp)}\n")
                    sys.stdout.flush()

            except json.JSONDecodeError as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {str(e)}"}}
                sys.stdout.write(f"{json.dumps(err_resp)}\n")
                sys.stdout.flush()
            except KeyboardInterrupt:
                break
            except Exception as e:
                sys.stderr.write(f"[{SERVER_NAME}] Server loop error: {e}\n")
                sys.stderr.flush()
