# 03 — Pagination followed the transport host

**Context:** Synthetic wrapper URL lab using a reserved example endpoint.

**Symptom:** Page one looked correct, but the next request no longer pointed at
the catalogue. Rewrapping its URL would send the rendering service its own host.

**Wrong hypothesis:** The next-page selector is wrong, or the target blocks page two.

**Proof:** No HTTP request is necessary. The response URL is
`https://proxy.example/?url=<encoded-target>`, while the next link is `page-2.html`.
A plain relative join produces `https://proxy.example/page-2.html`. The regression
expects `https://books.toscrape.com/catalogue/page-2.html` and fails against the
naive implementation. Inspecting that intermediate URL isolates the defect before
selectors, network behavior, or proxy reputation enter the picture.

**Fix:** Unwrap the known transport endpoint, resolve against the target URL,
validate the target origin, then encode exactly one wrapper at the boundary.
Decode each wrapper layer once so encoded query separators remain target data.
Reject missing or duplicate targets and excessive nesting.

**Verification:** Run the labeled broken test with `--runxfail` to repeat the
failure. `pytest tests/test_pagination.py -q -rx` runs the corrected regression,
encoded-query preservation, nested wrappers, plain targets, invalid input, and
cross-origin checks. The broken reproducer remains a strict expected failure.

**Prevention:** Name variables by their role: transport URL, target URL, next link.
Assert the resolved target independently before sending it to an API. A syntactically
valid URL is not evidence that it addresses the intended resource.
