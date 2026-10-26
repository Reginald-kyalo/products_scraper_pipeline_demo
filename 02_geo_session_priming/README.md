# 02 — Session priming with a region cookie

```bash
pytest tests/test_geo_session.py -q
# Explicit live run against public cookie endpoints
python 02_geo_session_priming/geo_session.py
```

`GeoSession` visits a landing page, asks the cookie endpoint to set `demo_region`,
and fetches the cookie echo endpoint with the same `requests.Session`. It checks
HTTP errors, enforces timeouts, rejects malformed region labels, and rejects
listing redirects rather than silently accepting a landing page. The context
manager closes the connection pool. Proxy settings from the surrounding shell are
disabled for this direct-connect demonstration.

The offline server mirrors the relevant public endpoint contract: cookie setup
returns a 302 with `Set-Cookie`, and the redirected request carries that cookie.
A new client has no inherited region. Tests use a real cookie jar and real local
HTTP requests rather than mocking Session internals.

The live command uses `https://httpbin.org/cookies/set` and `/cookies`; it prints
only whether the demonstration region persisted. A cookie label does not change
network egress geography. Verify country selection separately using the proxy's
controls and an independent IP diagnostic. The two concepts solve different problems.
