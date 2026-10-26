"""Demonstrate cookie continuity using public cookie endpoints."""

import re
from urllib.parse import urlsplit

import requests


class GeoSession:
    def __init__(self, base_url="https://httpbin.org", timeout=15):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
            raise ValueError("Expected an HTTP(S) base URL")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False

    def prime(self, region="demo-north"):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", region):
            raise ValueError("Expected a short region label")
        landing = self.session.get(self.base_url + "/", timeout=self.timeout)
        landing.raise_for_status()
        response = self.session.get(
            self.base_url + "/cookies/set",
            params={"demo_region": region},
            timeout=self.timeout,
        )
        response.raise_for_status()
        if not any(c.name == "demo_region" and c.value == region for c in self.session.cookies):
            raise RuntimeError("Priming endpoint did not set the demonstration cookie")

    def listings(self):
        if not any(c.name == "demo_region" for c in self.session.cookies):
            raise RuntimeError("Call prime before fetching listings")
        response = self.session.get(
            self.base_url + "/cookies",
            timeout=self.timeout,
            allow_redirects=False,
        )
        if 300 <= response.status_code < 400:
            raise RuntimeError("Listing redirected; prime a fresh session and inspect the region")
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.session.close()


if __name__ == "__main__":
    with GeoSession() as client:
        client.prime()
        result = client.listings()
        print("Region persisted:", result.get("cookies", {}).get("demo_region") == "demo-north")
