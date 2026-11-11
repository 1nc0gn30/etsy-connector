<p align="center">
  <img src="assets/hero-banner.svg" alt="Etsy Connector — Etsy Open API v3 Bridge, 13-Tag SEO Auditor, Fee/Margin Calculator & MCP Server" width="100%" />
</p>

# Etsy Connector

**Zero-dependency Python 3.10+ Etsy Open API v3 client, OAuth 2.0 PKCE helper, 13-tag SEO rank auditor, seller fee and net profit calculator, Printify/Gelato POD payload generator, loopback cockpit, and 8-tool MCP server.**

- **Zoth Studio v2 Dossier**: [https://zoth.nullai.tech/tools/etsy-connector](https://zoth.nullai.tech/tools/etsy-connector)
- **Default Loopback Endpoint**: `http://127.0.0.1:8108`
- **Runtime Dependencies**: Zero external Python runtime packages (100% Python `stdlib`)
- **License**: MIT (100% free and open-source)

---

## Overview

`etsy-connector` bridges Etsy Open API v3 storefront operations with deterministic local auditing and print-on-demand payload synthesis:

- **13-Tag & Title SEO Auditor**: Evaluates listing titles (`<=140` chars), search tags (`13` tags, `<=20` chars each, duplicate detection), and descriptions against Etsy search ranking constraints.
- **Fee & Net Margin Calculator**: Computes `$0.20` listing fees, `6.5%` transaction fees, `3% + $0.25` payment processing, optional `15%` Offsite Ads fees, POD base/shipping costs, net profit, and ROI.
- **Etsy Open API v3 & OAuth 2.0 PKCE**: Supports PKCE authorization code exchange, `0600` credential storage (`~/.etsy_connector_config.json`), competitor keyword search, shop profile updates, and dry-run-by-default draft listing creation (`confirm=true` required for live writes).
- **8-Tool MCP Server**: Exposes stdio JSON-RPC 2.0 tools for AI agents alongside a loopback HTTP cockpit on `127.0.0.1:8108`.

---

## Architecture

```text
src/etsy_connector/
├── client.py          # Stdlib Etsy Open API v3 client, OAuth 2.0 PKCE & simulation fallback
├── seo_engine.py      # 140-char title / 13-tag SEO rank auditor & Etsy fee/margin calculator
├── taxonomy.py        # Seller taxonomy category lookup for POD and digital goods
├── pod_bridge.py      # Printify / Gelato fulfillment payload builder for Etsy listings
├── mcp_server.py      # JSON-RPC 2.0 stdio MCP server exposing 8 Etsy & POD tools
├── web_cockpit.py     # Loopback HTTP API + browser cockpit (127.0.0.1:8108)
└── cli.py             # Unified CLI entrypoint (`etsy-connector`)
```

---

## Quickstart

```bash
git clone https://github.com/1nc0gn30/etsy-connector.git
cd etsy-connector
python3 -m pip install -e .

# Launch the loopback web cockpit on http://127.0.0.1:8108
python3 server.py --host 127.0.0.1 --port 8108
```

Or run via the CLI entrypoint:

```bash
etsy-connector serve --host 127.0.0.1 --port 8108
```

---

## CLI & MCP Usage

### CLI Subcommands

```bash
# View CLI help
etsy-connector --help

# Audit a listing title and 13 search tags
etsy-connector audit \
  --title "Grandma Garden Sweatshirt, Custom Wildflower Crewneck, Personalized Gift" \
  --tags "grandma sweatshirt,wildflower sweater,grandmas garden,custom crewneck,mom birthday gift,botanical shirt,plant lover gift,gift for grandma,grandkids names,mothers day gift,comfort colors tee,floral pullover,family tree shirt" \
  --json

# Calculate Etsy seller fees, POD base cost, and net profit margin
etsy-connector profit --retail 34.99 --pod 12.80 --ads --json

# Search active Etsy marketplace listings (uses deterministic simulation if unconfigured)
etsy-connector search --keywords "wildflower sweatshirt" --limit 5 --json

# Configure API credentials or run OAuth 2.0 PKCE authorization
etsy-connector config --key "<ETSY_KEYSTRING>" --shop "<SHOP_ID>"
etsy-connector auth --key "<ETSY_KEYSTRING>"

# Create a draft digital listing (dry-run unless --confirm is passed)
etsy-connector draft-digital --title "Printable Wall Art" --desc "300 DPI PDF" --price 6.99 --tags "wall art,printable pdf"

# Launch the stdio MCP server
etsy-connector mcp
```

### ZothOS v3.4.0 CLI Integration

On ZothOS v3.4.0 workstations, `etsy-connector` and `etsy-connector-tui` are installed in `/usr/local/bin/`:

```bash
etsy-connector profit --retail 34.99 --pod 12.80 --json
etsy-connector-tui --json
etsy-connector serve --port 8108
```

### Model Context Protocol (MCP) Tools

```json
{
  "mcpServers": {
    "etsy-connector": {
      "command": "etsy-connector",
      "args": ["mcp"]
    }
  }
}
```

| MCP Tool | Description |
| :--- | :--- |
| `etsy_search_listings` | Search active Etsy listings for competitor pricing and keyword research |
| `etsy_audit_listing_seo` | Audit title (`<=140` chars), 13 tags (`<=20` chars), and description |
| `etsy_calculate_profit_margins` | Compute Etsy listing/transaction/processing/offsite-ad fees and net margin |
| `etsy_get_taxonomy_categories` | Look up Etsy seller taxonomy IDs and keyword mappings |
| `etsy_create_draft_listing` | Create a draft Etsy listing (dry-run unless `confirm=true`) |
| `etsy_upload_listing_image` | Attach a mockup or artwork image to an Etsy listing |
| `etsy_get_shop_details` | Retrieve shop profile, active listing count, and review score |
| `etsy_generate_pod_payload` | Build a Printify/Gelato fulfillment payload linked to an Etsy blueprint |

---

## HTTP API Reference

When running on `http://127.0.0.1:8108`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health`, `/api/health` | Service health status, port, configuration state, and uptime |
| `GET` | `/api/stats` | Audit, profit calculation, search, and POD payload counters |
| `GET` | `/api/taxonomy` | Supported Etsy seller taxonomy categories |
| `GET` | `/api/blueprints` | POD product blueprints and print specifications |
| `GET` | `/api/mcp/tools` | Registered MCP tool schemas |
| `POST` | `/api/audit` | Run 13-tag and title SEO audit |
| `POST` | `/api/profit` | Run Etsy fee and POD margin breakdown |
| `POST` | `/api/search` | Search Etsy marketplace listings |
| `POST` | `/api/pod` | Generate Printify/Gelato product creation JSON payload |
| `POST` | `/api/create-draft` | Create draft Etsy listing (dry-run unless `confirm=true`) |
| `POST` | `/api/credentials` | Save Etsy API key, OAuth token, and shop ID (`0600` permissions) |

---

## Testing & Verification

```bash
# Run the pytest suite
PYTHONPATH=src python3 -m pytest -q

# Scan repository with gitleaks
gitleaks detect --source . --no-banner --redact
```

---

## Support

Etsy Connector is 100% free and open-source software. Optional community support is available via [Buy Us a Coffee (Stripe)](https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X).

## License

MIT License — Copyright (c) 2026 [1nc0gn30](https://1nc0gn30.si) (`@1nc0gn30`) & [NullAI](https://nullai.tech). See [LICENSE](LICENSE) for full text.
