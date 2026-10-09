# 🌸 Etsy Connector for Antigravity & Sovereign AI Agents

[![Audit](https://img.shields.io/badge/guardrail-100%25%20passed-emerald)](https://etsy.nullai.tech)
[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.10%2B-gold)](https://python.org)
[![Zero Pip](https://img.shields.io/badge/dependencies-0%20external-purple)](https://nullai.tech)

Autonomous Etsy Open API v3 and Print-on-Demand (POD) bridge for **Google Antigravity** AI agents. Exposes 8 Model Context Protocol (MCP) tools for competitor search, 13-tag SEO ranking audits, exact fee & profit modeling, and automated Printify fulfillment payloads.

---

## ⚡ 8 Model Context Protocol (MCP) Tools

When registered in `~/.gemini/config/mcp_config.json`, Antigravity gains immediate access to:

1. `etsy_search_listings`: Real-time competitor analysis, pricing, and tag discovery.
2. `etsy_audit_listing_seo`: 13-tag (≤20 chars) and Title (≤140 chars) ranking algorithm auditor.
3. `etsy_calculate_profit_margins`: Precise breakdown of Etsy fees, POD production costs, and net margin.
4. `etsy_get_taxonomy_categories`: Etsy category taxonomy ID lookup.
5. `etsy_create_draft_listing`: Programmatic draft listing generation.
6. `etsy_upload_listing_image`: Multi-angle mockup and photo uploads.
7. `etsy_get_shop_details`: Storefront metrics, reviews, and active inventory tracking.
8. `etsy_generate_pod_payload`: 1-click Printify/Gelato product fulfillment JSON generator.

---

## 🚀 Quick Start

### 1. Antigravity MCP Setup
Add to `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "etsy-connector": {
      "command": "/home/zoth/NullAITech/etsy-connector/bin/etsy-connector",
      "args": ["mcp"],
      "env": {
        "PYTHONPATH": "/home/zoth/NullAITech/etsy-connector/src"
      }
    }
  }
}
```

### 2. Run CLI Operations
```bash
# Calculate net margins for a $38.99 sweatshirt with $15.50 POD cost:
./bin/etsy-connector profit --retail 38.99 --pod 15.50

# Audit an Etsy listing title and tags:
./bin/etsy-connector audit --title "Grandma Garden Sweatshirt" --tags "grandma gift,garden crewneck,floral sweater"

# Launch Web Cockpit on port 8108:
./bin/etsy-connector serve --port 8108
```

---

## 📜 Attribution & License
Engineered by **Neal Frazier Tech** ([@1nc0gn30](https://github.com/1nc0gn30)) • [NullAI Platform](https://nullai.tech)
MIT License.
