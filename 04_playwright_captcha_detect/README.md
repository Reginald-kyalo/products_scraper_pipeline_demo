# 04 — Evidence before escalation

```bash
python -m playwright install chromium
python 04_playwright_captcha_detect/classifier.py --fixture tests/fixtures/captcha.html
python 04_playwright_captcha_detect/classifier.py --fixture tests/fixtures/empty.html
DEMO_BROWSER_TEST=1 pytest tests/test_classifier.py -q
# Explicit live practice snapshot
python 04_playwright_captcha_detect/classifier.py --url https://books.toscrape.com/
```

The browser captures one DOM snapshot and the main navigation status. An offline
fixture uses `set_content`, aborts all subresource requests, and can supply a
synthetic status with `--status 429`. `--output /tmp/triage.json` saves only the
classification and generic evidence. No body, cookie, URL query, or screenshot is
written into the report.

Priority matters: 429 means slow down even if the body contains a verification
widget. Generic verification elements without expected content suggest CAPTCHA; browser-check text suggests
a JavaScript challenge. Otherwise an expected-content count helps distinguish an
apparently healthy page from a suspected empty shell. A small body alone is not
evidence of a decoy. Use `--selector .quote` for the quotes practice target.

Recommendations deliberately require judgment. Repeated verification may justify
an authorized residential test; a browser challenge may justify checking an
unblocker service's capabilities. A 403 or missing expected content calls for
inspection before an IP change. Legitimate empty pages, changed selectors, access
policies, and incomplete rendering remain alternative explanations. Nothing is
solved, retried, or switched automatically. Waiting for meaningful readiness and
checking client-side API responses are follow-up investigations, beyond this snapshot.

When verification signals coexist with expected content, the result stays unknown
and recommends inspection. Script, style, template, and explicitly hidden prompt
text is excluded. CSS visibility and quoted visible prose still require human review.
