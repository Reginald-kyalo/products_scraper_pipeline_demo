# Scraping support demos

Five small labs for reviewing proxy troubleshooting, HTTP sessions, URL debugging,
page triage, and Scrapy compatibility. All examples were rebuilt against public
practice targets. Test pages are authored synthetic fixtures. No credentials are needed.

This repository demonstrates selected engineering patterns from a larger private
scraping project. All examples were independently rebuilt using public practice
targets and synthetic fixtures. Proprietary implementations, retailer-specific
findings, datasets, and credentials are excluded.

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

For a 20-minute review, start with [pagination](03_render_tier_pagination/README.md),
then the [proxy decision tree](docs/troubleshooting-proxies.md) and
[five postmortems](docs/postmortems/). The postmortems describe these synthetic
labs; they do not claim production incidents or measured performance.

Live examples fetch one practice page with concurrency one and a delay. A region
cookie is application state, not proof of IP location. Classifier recommendations
are hypotheses for an operator to investigate, not automatic escalation or a claim
that any proxy class guarantees access. Secrets belong in local configuration;
share only redacted diagnostics.
