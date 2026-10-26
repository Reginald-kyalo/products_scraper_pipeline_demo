# Scraping engineering — public work sample

[![Offline demos CI](https://github.com/Reginald-kyalo/products_scraper_pipeline_demo/actions/workflows/ci.yml/badge.svg)](https://github.com/Reginald-kyalo/products_scraper_pipeline_demo/actions/workflows/ci.yml)

My larger scraping project contains proprietary implementations, datasets, and
retailer-specific integrations that I cannot publish. I created this repository
to provide reviewable code samples when sharing my work for job applications.

These five examples demonstrate selected engineering approaches from that project:
proxy handling, session management, pagination debugging, page classification, and
framework compatibility. Each was independently rebuilt against public practice
targets and synthetic fixtures, so reviewers can inspect the code, run the tests,
and evaluate the reasoning without access to the private system. No credentials
are needed.

For a quick review, start here:

1. [Pagination debugging](03_render_tier_pagination/README.md): reproduce the bug,
   inspect the wrong URL, then run the regression against the fix.
2. [Proxy troubleshooting guide](docs/troubleshooting-proxies.md): follow the
   diagnostic process from symptom to a verified fix.
3. [Async middleware migration](05_async_middleware_scrapy213/README.md): compare
   the before/after implementations and the real Scrapy version tests.

The pagination example runs offline with Python alone:

```bash
python3 03_render_tier_pagination/pagination.py
```

Its first two output lines show the fault and the corrected target:

```text
Naive: https://proxy.example/page-2.html
Fixed: https://books.toscrape.com/catalogue/page-2.html
```

| Lab | What to review | Run from this directory |
| --- | --- | --- |
| [01 Rotation](01_proxy_rotation_scrapy/) | Bounded retries, nonblocking backoff, slot health | `python 01_proxy_rotation_scrapy/demo.py --offline` |
| [02 Session](02_geo_session_priming/) | Landing → cookie setup → listing continuity | `pytest tests/test_geo_session.py -q` |
| [03 Pagination](03_render_tier_pagination/) | Reproduce a wrapper URL bug, then fix the URL boundary | `python 03_render_tier_pagination/pagination.py` |
| [04 Page triage](04_playwright_captcha_detect/) | Status + DOM evidence → conservative next action | See browser command below |
| [05 Async migration](05_async_middleware_scrapy213/) | Sync reproducer vs streaming fix in a real engine | `python 05_async_middleware_scrapy213/demo.py --offline` |

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest -q
# Optional browser integration: synthetic local DOM, no public requests
python -m playwright install chromium
DEMO_BROWSER_TEST=1 pytest tests/test_classifier.py -q
python 04_playwright_captcha_detect/classifier.py --fixture tests/fixtures/captcha.html
```

Python 3.11 or 3.13. CI declares Scrapy 2.12.0, 2.13.4, and 2.16.0 on both Python
versions, plus Chromium integration. Tests use a loopback HTTP server, synthetic
responses, and `data:` pages; public targets are contacted only by explicit live runs.
The intentionally broken pagination regression is a strict expected failure.

The [five postmortems](docs/postmortems/) explain the symptom, initial hypothesis,
proof, fix, and prevention for each lab. They describe synthetic demonstrations;
the original implementations, retailer-specific findings, datasets, and credentials
remain private. These samples provide selected evidence of engineering skills,
rather than the full private system or its production history.

Live examples fetch one practice page with concurrency one and a delay. A region
cookie is application state, not proof of IP location. Classifier recommendations
are hypotheses for an operator to investigate, not automatic escalation or a claim
that any proxy class guarantees access. Secrets belong in local configuration;
share only redacted diagnostics.
