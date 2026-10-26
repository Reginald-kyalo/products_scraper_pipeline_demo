# Verification record

Verified locally on Python 3.13, 2026-10-26:

| Environment | Command | Result |
| --- | --- | --- |
| Scrapy 2.12.0 + legacy constraints | `python -m pytest -q` | 50 passed, 1 browser test skipped, 1 expected failure |
| Scrapy 2.13.4 | `python -m pytest -q` | 50 passed, 1 browser test skipped, 1 expected failure |
| Scrapy 2.16.0 + Chromium | `DEMO_BROWSER_TEST=1 python -m pytest -q` | 51 passed, 1 expected failure |

`ruff check .`, `ruff format --check .`, and `pip check` passed. The browser test
uses synthetic local HTML; cookie tests bind only to loopback. No public site,
proxy subscription, or credential is needed for the suite. Live practice examples
are opt-in and were not used as evidence for these results.

The expected failure is the intentionally broken pagination reproducer. Running
`pytest tests/test_pagination.py::test_broken_reproducer --runxfail -q` fails with
the proxy origin where the catalogue origin is expected. The corrected regression
passes. The initial failing tests were run before the implementations; the final
review added and reproduced six further failures before fixing ambiguous page
signals and invalid URL handling.

A subsequent review reproduced two over-limit `Retry-After` failures before fixing
the early-retry behavior. Tests now cover server delays within the limit and stop
automatic retries above it, for both seconds and HTTP-date headers. The nested URL
test uses an independent two-layer fixture; it was also checked against a temporary
single-layer decoder and failed as expected. The decoder source was not changed.

Hosted CI has also passed all six Python/Scrapy combinations and the separate
Chromium job: [verified run for commit ccfe1e4](https://github.com/Reginald-kyalo/products_scraper_pipeline_demo/actions/runs/40337523135).
This includes Python 3.11, which was not available locally. The
[current workflow status](https://github.com/Reginald-kyalo/products_scraper_pipeline_demo/actions/workflows/ci.yml)
tracks subsequent revisions. Install the legacy row with `-c constraints-legacy.txt`
as shown in the migration README.

All modules were written in this independent repository without importing source
files, data, or Git history from another project. Fixtures are authored examples.
The repository was prepared for public sharing. Gitleaks 8.24.3 and a separate
proprietary-name/provider/cookie denylist scan found zero matches in the exact staged
contents before the first commit. The resulting Git history also passed Gitleaks,
and both checks were repeated before publication. Neither automated check replaces
human review of what is appropriate to share.
