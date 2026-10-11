"""Live-mode safety: dry-run writes, no fake success, private credentials, no token echo,
cross-origin blocking. Uses a local fake Etsy API; never contacts Etsy."""
import json, os, socket, stat, sys, tempfile, threading, unittest, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from etsy_connector import client as client_mod
from etsy_connector.client import EtsyClient
from etsy_connector import web_cockpit
from etsy_connector.web_cockpit import EtsyCockpitHandler, _is_local_origin

FAKE_KEY, FAKE_TOKEN = "keystring-TEST-0000", "tok-TEST-SECRET-1111"


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class FakeEtsy(BaseHTTPRequestHandler):
    calls, status = [], 201
    def log_message(self, *a): pass
    def do_POST(self):
        FakeEtsy.calls.append(self.path)
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = json.dumps({"listing_id": 42, "state": "draft"}).encode()
        self.send_response(FakeEtsy.status); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


class TestEtsyLiveSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = HTTPServer(("127.0.0.1", free_port()), FakeEtsy)
        threading.Thread(target=cls.fake.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.fake.shutdown()

    def live_client(self):
        c = EtsyClient(api_key=FAKE_KEY, access_token=FAKE_TOKEN, shop_id="123", simulate=False)
        c.base_url = f"http://127.0.0.1:{self.fake.server_port}"
        return c

    def setUp(self):
        FakeEtsy.calls.clear(); FakeEtsy.status = 201
        os.environ.pop("ETSY_ALLOW_LIVE_WRITES", None)

    def test_live_write_is_dry_run_by_default(self):
        res = self.live_client().create_draft_listing("Mug", "d", 20.0)
        self.assertTrue(res["dry_run"])
        self.assertEqual(FakeEtsy.calls, [], "dry run must not contact the API")
        self.assertNotIn(FAKE_TOKEN, json.dumps(res))

    def test_confirm_sends(self):
        res = self.live_client().create_draft_listing("Mug", "d", 20.0, confirm=True)
        self.assertEqual(res["listing_id"], 42)
        self.assertEqual(FakeEtsy.calls, ["/shops/123/listings"])

    def test_env_opt_in_sends(self):
        with mock.patch.dict(os.environ, {"ETSY_ALLOW_LIVE_WRITES": "1"}):
            self.live_client().create_draft_listing("Mug", "d", 20.0)
        self.assertEqual(len(FakeEtsy.calls), 1)

    def test_auth_failure_on_write_raises_not_fake_success(self):
        FakeEtsy.status = 401
        with self.assertRaises(RuntimeError):
            self.live_client().create_draft_listing("Mug", "d", 20.0, confirm=True)

    def test_network_failure_on_write_raises(self):
        c = self.live_client(); c.base_url = f"http://127.0.0.1:{free_port()}"  # nothing listening
        with self.assertRaises(RuntimeError) as cm:
            c.create_draft_listing("Mug", "d", 20.0, confirm=True)
        self.assertNotIn(FAKE_TOKEN, str(cm.exception))

    def test_credentials_file_is_private(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "etsy.json"
            with mock.patch.object(client_mod, "CONFIG_PATH", cfg):
                EtsyClient(simulate=True).save_credentials(FAKE_KEY, FAKE_TOKEN, "1")
            self.assertEqual(stat.S_IMODE(cfg.stat().st_mode), 0o600)


class TestCockpitHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        EtsyCockpitHandler.client = EtsyClient(api_key=FAKE_KEY, access_token=FAKE_TOKEN, shop_id="1", simulate=True)
        EtsyCockpitHandler.start_time = 0
        EtsyCockpitHandler.stats = {"audits_performed": 0, "profit_calculations": 0, "pod_payloads_generated": 0, "searches_executed": 0}
        cls.srv = ThreadingHTTPServer(("127.0.0.1", free_port()), EtsyCockpitHandler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, path, data=None, origin=None):
        h = {"Content-Type": "application/json"}
        if origin: h["Origin"] = origin
        r = urllib.request.Request(self.base + path, data=json.dumps(data).encode() if data is not None else None, headers=h)
        try:
            with urllib.request.urlopen(r, timeout=5) as resp:
                return resp.status, resp.read().decode(), dict(resp.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(), dict(e.headers)

    def test_health_and_stats_never_echo_tokens(self):
        for path in ("/api/health", "/api/stats"):
            status, body, _ = self.req(path)
            self.assertEqual(status, 200)
            self.assertNotIn(FAKE_TOKEN, body); self.assertNotIn(FAKE_KEY, body)

    def test_cross_origin_post_blocked(self):
        with mock.patch.object(client_mod, "CONFIG_PATH", Path(tempfile.gettempdir()) / "never-written.json"):
            status, _, _ = self.req("/api/credentials", {"api_key": "x", "access_token": "y"}, origin="https://evil.example")
        self.assertEqual(status, 403)

    def test_local_origin_allowed_and_cors_not_wildcard(self):
        status, _, headers = self.req("/api/audit", {"title": "t", "tags": [], "description": "d"}, origin=self.base)
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), self.base)

    def test_origin_helper(self):
        self.assertTrue(_is_local_origin(None))
        self.assertTrue(_is_local_origin("http://localhost:8108"))
        for bad in ("https://evil.example", "null", "http://127.0.0.1.evil.com", "file://"):
            self.assertFalse(_is_local_origin(bad), bad)


if __name__ == "__main__":
    unittest.main()
