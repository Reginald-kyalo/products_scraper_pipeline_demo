# 03 — Target URL vs transport URL

A rendering API can report its own wrapper URL as `response.url`. Joining a
relative next link against that URL yields `https://proxy.example/page-2.html`,
losing both the target host and `/catalogue/`. Wrapping that result again creates
a request for the proxy's page, not the target's next page.

```bash
# RED: intentionally exits 1; inspect actual vs expected target
pytest tests/test_pagination.py::test_broken_reproducer --runxfail -q
# GREEN: fixed behavior plus the labeled strict expected failure
pytest tests/test_pagination.py -q -rx
python 03_render_tier_pagination/pagination.py
```

The regression was run against the naive implementation before the fix. The
broken reproducer remains separate so a reviewer can repeat the failure without
editing working code. The fixed regression asserts the target literal independently.

The corrected sequence is `unwrap_target(response.url)` → resolve relative link →
check origin → wrap once at the transport boundary. Query decoding happens once
per known wrapper layer, preserving percent-encoded target query values. Unknown
hosts with a query parameter named `url` are left alone. Missing or duplicate target
parameters, unsupported schemes, embedded credentials, cross-origin pagination,
and excessive nesting raise errors. The wrapper hostname is reserved example
configuration and is never contacted.

In a real integration, configure the exact documented API endpoint and its target
parameter, and decide how redirects should update the canonical target base. This
lab handles the URL contract only; it is not an HTTP proxy client.
