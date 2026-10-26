# 05 — A real async middleware migration ticket

```bash
python 05_async_middleware_scrapy213/demo.py --offline
pytest tests/test_async_middleware.py -q
# Intentionally exits 1 on 2.16; 2.12 accepts it, 2.13 warns
python 05_async_middleware_scrapy213/demo.py --offline --legacy
```

The runner uses Scrapy's engine and a `data:` response with one synthetic book.
Its callback yields asynchronously. The legacy middleware uses a synchronous
`for`; the replacement uses `async def` and `async for`, yielding each item as it
arrives. Requests pass through unchanged. A stream failure after one item does not
discard that earlier item. The runner returns nonzero when startup fails or no
item is produced, so Scrapy's normal process exit behavior cannot hide failure.

| Scrapy | Legacy sync-only middleware | Async replacement |
| --- | --- | --- |
| 2.12.0 | Framework adapts async output; buffering may occur | Streaming |
| 2.13.4 | Accepted with deprecation warning | Streaming |
| 2.16.0 | Rejected during middleware setup | Streaming |

CI declares this matrix on Python 3.11 and 3.13 and tests actual engine output,
not just direct method calls. To reproduce another row locally, create a fresh
venv and install `-r requirements-dev.txt 'Scrapy==2.12.0' -c constraints-legacy.txt` (or the chosen version).
The dependency range allows each pinned CI version. Default installation selects
the newest release below 2.17, keeping this compatibility exercise bounded.

This migration concerns **spider** output middleware. Downloader hooks and the
2.13 `start()` migration are separate interfaces. The example inherits Scrapy's
default start implementation to keep that concern out of the reproduction.

Sources: [2.13 release notes](https://docs.scrapy.org/en/2.13/news.html),
[2.16 release notes](https://docs.scrapy.org/en/2.16/news.html),
[async spider output](https://docs.scrapy.org/en/2.16/topics/spider-middleware.html).

The shared URL utility dependency is pinned to 2.3.1: a fresh legacy installation
with 2.5.0 fails on an import of a removed private helper, before middleware loads.
Keeping that dependency constant isolates this migration from unrelated upgrades.

The 2.12 row also uses `constraints-legacy.txt` to hold Twisted at 24.11.0.
Twisted 26 removes a TLS helper that 2.12 imports. The other rows retain current
networking dependencies; this is a middleware migration lab, not a claim that an
old framework supports every future dependency release.
