# 05 — An upgrade rejected synchronous spider middleware

**Context:** Offline migration reproduction across pinned framework versions.

**Symptom:** Middleware that runs under an older framework is rejected during
setup after an upgrade. The crawler exports no items.

**Wrong hypothesis:** The page structure changed, or the proxy stopped working.

**Proof:** The reproduction uses a synthetic `data:` page, eliminating both the
public network and changing HTML. A sync-only `process_spider_output` uses `for`
over results. Passing an async iterator directly raises a type error. The real
engine tests distinguish older adaptation, deprecation, and removal; a unit call
alone would not establish which framework version accepts the middleware.

**Fix:** Make the spider output hook an async generator and consume results with
`async for`. Yield items as they arrive and preserve request objects. The runner
also returns nonzero for setup failures or missing output, making failure visible
to a support script.

**Verification:** `pytest tests/test_async_middleware.py -q` checks stream behavior,
request preservation, partial output before an error, and real-engine export.
CI pins 2.12.0, 2.13.4, and 2.16.0 rather than assuming every release behaves alike.

**Prevention:** Keep a small offline compatibility matrix and inspect deprecation
warnings before upgrading. Confirm which interface changed: spider output hooks,
downloader hooks, and start-request hooks have different contracts. Cite the
release notes alongside the reproducer so the next maintainer can verify the boundary.
