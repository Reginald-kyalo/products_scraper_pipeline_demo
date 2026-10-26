# 02 — A successful page from the wrong session state

**Context:** Synthetic local cookie server modeled on public cookie endpoints.

**Symptom:** A listing request without a region cookie redirects to a landing
page. Following redirects blindly would make the request look successful while
returning the wrong content.

**Wrong hypothesis:** A missing listing means the page requires browser rendering.

**Proof:** The local server returns a 302 and `Set-Cookie` during setup. A real
`requests.Session` follows that redirect and sends the cookie on the listing request.
The same listing fails in a fresh client. The variable is session state; neither
JavaScript nor a different network route is involved.

**Fix:** Visit the landing page, complete region setup, and reuse one cookie jar.
Reject an unexpected listing redirect and HTTP errors before parsing. Close the
session after use and enforce timeouts.

**Verification:** `pytest tests/test_geo_session.py -q` uses real local HTTP and
cookie handling, checks that the configured region persists, verifies fresh-session
isolation, and rejects malformed cookie labels. The public run prints only a
boolean continuity result.

**Prevention:** Separate application region state from IP geography. A demonstration
cookie can show continuity but cannot establish where a request exits the network.
Add a state check before interpreting a landing page as an empty listing.
