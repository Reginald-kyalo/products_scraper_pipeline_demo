import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from geo_session import GeoSession


@pytest.fixture
def cookie_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path)
            if path.path == "/cookies/set":
                region = parse_qs(path.query)["demo_region"][0]
                self.send_response(302)
                self.send_header("Set-Cookie", f"demo_region={region}; Path=/")
                self.send_header("Location", "/cookies")
                self.end_headers()
            elif path.path == "/cookies":
                cookie = self.headers.get("Cookie", "")
                if not cookie:
                    self.send_response(302)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"cookie": cookie}).encode())
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Practice landing page")

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()
    server.server_close()


def test_unprimed_listing_fails_instead_of_silently_following_home(cookie_server):
    with GeoSession(cookie_server) as client:
        with pytest.raises(RuntimeError, match="prime"):
            client.listings()


def test_real_cookie_jar_survives_prime_redirect_and_listing(cookie_server):
    with GeoSession(cookie_server) as client:
        client.prime("demo-north")
        assert client.listings()["cookie"] == "demo_region=demo-north"
        assert isinstance(client.session, requests.Session)


def test_fresh_session_has_no_inherited_region(cookie_server):
    with GeoSession(cookie_server) as first:
        first.prime("demo-south")
        assert "demo-south" in first.listings()["cookie"]
    with GeoSession(cookie_server) as second:
        with pytest.raises(RuntimeError):
            second.listings()


@pytest.mark.parametrize("region", ["", "bad;region", "bad\r\nvalue"])
def test_rejects_malformed_cookie_value(cookie_server, region):
    with GeoSession(cookie_server) as client:
        with pytest.raises(ValueError):
            client.prime(region)
