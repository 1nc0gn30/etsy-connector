"""Servers must bind to localhost unless network exposure is explicitly requested."""
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from etsy_connector.web_cockpit import _default_bind_host


class TestBindHost(unittest.TestCase):
    def test_default_is_localhost(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_default_bind_host(), "127.0.0.1")

    def test_explicit_opt_in(self):
        with mock.patch.dict(os.environ, {"ZOTH_BIND_HOST": "0.0.0.0"}, clear=True):
            self.assertEqual(_default_bind_host(), "0.0.0.0")
        with mock.patch.dict(os.environ, {"HOST": "192.168.1.5"}, clear=True):
            self.assertEqual(_default_bind_host(), "192.168.1.5")

    def test_hostname_in_HOST_is_ignored(self):
        # zsh exports HOST=<hostname>; that must not silently expose the server.
        with mock.patch.dict(os.environ, {"HOST": "zoth-pill"}, clear=True):
            self.assertEqual(_default_bind_host(), "127.0.0.1")
        with mock.patch.dict(os.environ, {"HOST": "localhost"}, clear=True):
            self.assertEqual(_default_bind_host(), "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
