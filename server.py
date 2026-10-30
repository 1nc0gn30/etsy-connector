#!/usr/bin/env python3
"""Etsy Connector - Root Server Launcher
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""
import sys
from pathlib import Path
import argparse

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from etsy_connector.web_cockpit import run_server

def main():
    parser = argparse.ArgumentParser(description="Etsy Connector Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8108, help="Port to bind to")
    args = parser.parse_args()

    public_dir = Path(__file__).resolve().parent / "public"
    run_server(port=args.port, public_dir=public_dir, host=args.host)

if __name__ == "__main__":
    main()
