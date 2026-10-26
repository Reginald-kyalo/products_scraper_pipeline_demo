# 01 — Proxy rotation and bounded recovery

The downloader middleware rotates round-robin per request. A 403, 429, 503, or a
small generic challenge prompt triggers at most two retries. Each retry waits
without blocking the reactor; exponential delay and `Retry-After` are capped.
Transport timeouts and connection failures share the same budget. Other exceptions
propagate. `dont_retry` opts a request out.

```bash
python 01_proxy_rotation_scrapy/demo.py --offline
pytest tests/test_rotation.py -q
# Explicit live practice crawl (direct connection unless locally configured)
python 01_proxy_rotation_scrapy/demo.py
```

Offline mode uses a fake download handler returning 429, 429, then a synthetic
200. It traverses Scrapy's real downloader stack and exports one book to `/tmp`.
No socket or proxy is contacted. The close signal reports two bans and one success.

For a live run, `DEMO_PROXY_URLS` accepts a comma-separated list of HTTP(S) proxy
URLs. Set it locally without putting credentials in shell history or the repository.
Empty configuration means direct mode. Register this middleware at priority 610,
before the built-in HTTP proxy middleware at 750, and disable the built-in retry
middleware so retry budgets cannot multiply. The supplied runner does both.

`DEMO_MAX_RETRIES`, `DEMO_BASE_DELAY`, and `DEMO_MAX_DELAY` are Scrapy settings.
The defaults are 2, 1 second, and 30 seconds. A server delay longer than the cap
requires an operator pause; it is not permission to keep retrying sooner indefinitely.
For sustained 429s, stop the crawl and reduce the overall request rate.

The health scoreboard records successes, bans, and transport errors by slot index;
it never logs proxy URLs. This small demo does not implement distributed cooldowns,
health-weighted allocation, jitter, sticky sessions, or production credential storage.
Normal HTTP errors are not counted as successful proxy responses. Other Scrapy
logging and external libraries need their own redaction review before real use.
