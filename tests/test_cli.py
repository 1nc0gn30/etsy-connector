"""CLI and TUI regression tests for etsy-connector v2.6.0."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN_CLI = REPO_ROOT / "bin" / "etsy-connector"
BIN_TUI = REPO_ROOT / "bin" / "etsy-connector-tui"


class TestEtsyCliAndTui(unittest.TestCase):
    def _run(self, exe: Path, *args: str):
        env = dict(os.environ)
        env["ZOTH_REPO_DIR"] = str(REPO_ROOT)
        return subprocess.run(
            [sys.executable, str(exe), *args],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )

    def test_cli_json_manifest_no_home_leak(self):
        proc = self._run(BIN_CLI, "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("/home/", proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["tool"], "etsy-connector")
        self.assertEqual(data["version"], "2.6.0")
        self.assertIn("desktop", data["commands"])
        self.assertIn("pod", data["commands"])

    def test_cli_status_and_desktop(self):
        st = self._run(BIN_CLI, "--status", "--json")
        self.assertEqual(st.returncode, 0, st.stderr)
        self.assertNotIn("/home/", st.stdout)
        sdata = json.loads(st.stdout)
        self.assertEqual(sdata["version"], "2.6.0")
        self.assertEqual(sdata["mcp_tool_count"], 8)

        dk = self._run(BIN_CLI, "desktop", "--no-browser")
        self.assertEqual(dk.returncode, 0, dk.stderr)
        ddata = json.loads(dk.stdout)
        self.assertTrue(ddata["ok"])

    def test_cli_profit_12_and_pod_gelato(self):
        p = self._run(BIN_CLI, "profit", "--retail", "38.99", "--pod", "15.50", "--offsite-ads-rate", "0.12", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        pdata = json.loads(p.stdout)
        self.assertEqual(pdata["offsite_ads_rate"], 0.12)
        self.assertGreater(pdata["break_even_price"], 0)

        g = self._run(BIN_CLI, "pod", "--provider", "gelato", "--blueprint", "fine_art_poster_18x24", "--title", "Poster")
        self.assertEqual(g.returncode, 0, g.stderr)
        gdata = json.loads(g.stdout)
        self.assertEqual(gdata["provider"], "gelato")

    def test_tui_once_json_no_home_leak(self):
        proc = self._run(BIN_TUI, "--once", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("/home/", proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["version"], "2.6.0")
        self.assertEqual(data["mcp_tools"], 8)
        self.assertIn("offsite_12pct", data["margin_tiers"])
        self.assertGreaterEqual(len(data["braille_meter"]), 4)


if __name__ == "__main__":
    unittest.main()
