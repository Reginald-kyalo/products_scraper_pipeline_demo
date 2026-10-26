# 04 — HTTP success was mistaken for usable content

**Context:** Authored HTML fixtures and a local Playwright DOM snapshot.

**Symptom:** A response can be 200 and still contain only a verification prompt
or an empty shell, producing no useful records.

**Wrong hypothesis:** Every empty parse is an IP ban, so the client should rotate
immediately and repeatedly.

**Proof:** Separate fixtures represent a normal catalogue, verification widget,
JavaScript prompt, and empty page. The status-and-DOM tests distinguish those cases.
A 429 takes precedence even when the body also contains a verification widget.
A book article containing the word “captcha” remains healthy when expected content
is present, avoiding a simplistic keyword verdict.

**Fix:** Combine main-navigation status, generic DOM signals, and an explicit
expected-content count. Treat empty-shell detection as a hypothesis with alternatives.
Return evidence and a recommendation, leaving the operator to decide whether to
slow down, investigate an IP change, or assess another service class.

**Verification:** `pytest tests/test_classifier.py -q` covers classification and
priority. With Chromium installed, `DEMO_BROWSER_TEST=1` also exercises the browser
adapter against a real local DOM. Fixture subresource requests are aborted.

**Prevention:** Verify selectors and rendering readiness before escalation. Record
what was observed separately from the proposed remedy. Do not assume a single
snapshot proves deliberate deception or that a more expensive proxy will fix it.
