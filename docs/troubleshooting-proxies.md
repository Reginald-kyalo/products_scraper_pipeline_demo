# Proxy troubleshooting: a support decision tree

Start with one failing request, one expected result, and a small request budget.
Use a public diagnostic endpoint before testing the application. Record the time,
HTTP status, redirect chain, elapsed time, and whether the expected content was
present. Keep credentials, authentication headers, full cookie jars, and sensitive
query strings out of a ticket. A useful report lets another engineer reproduce the
failure without access to the customer's secrets.

## 1. Did an HTTP response arrive?

**No → separate connection, TLS, and application failures.** A DNS error points to
hostname resolution. A connection refusal or timeout points to reachability or an
unavailable listener. A certificate error needs a trust-chain investigation; turning
off verification can conceal the actual fault. Check proxy scheme, port, account
status, and a short connection timeout. Test the same public endpoint directly and
through one proxy, changing only that variable. If both fail, investigate the local
network and endpoint before replacing the proxy pool.

**Yes → identify which hop generated it.** A 407 normally calls for proxy
authentication checks; a 401 is an origin authentication problem. Check the account's
expected authentication method and any IP allowlist. Do not paste the configured
proxy URL into logs. Repeatedly rotating an invalid credential will not repair it.
Ask for a redacted configuration shape and the status instead of a raw environment dump.

## 2. Is the failure a rate limit?

**429 → stop the retry storm.** Inspect `Retry-After`, request rate, concurrency,
and whether several clients share a budget. Reduce concurrency and introduce
bounded backoff. The rotation demo deliberately disables the framework's other
retry middleware: two independent retry loops can multiply traffic. A server delay
longer than the client's delay cap stops automatic retries for that request and
calls for the operator to pause the job; the cap does not shorten the server's
requested wait. A limited, lower-rate experiment should change the
result before declaring that IP reputation is the cause.

**403 or 503 → inspect the body and headers.** Either can indicate a block, but
neither proves one. Access policy, maintenance, and upstream errors are alternatives.
Compare a normal practice page with the failure and classify generic challenge
signals. Keep response bodies local unless reviewed for sensitive information.
Use status and generic evidence summaries in the initial ticket.

## 3. Does the application see the intended session and location?

**Redirect to a landing page, wrong region, or missing listing → check session
continuity first.** Follow the first navigation separately and inspect the redirect
chain. Was the required setup completed? Did the server set a cookie, and did the
next request send it? Check domain, path, expiry, and session reuse. The cookie lab
uses a real local server to demonstrate why a new session loses that state. Treat
an unexpected listing redirect as a failure rather than parsing a successful-looking
landing page.

**Cookie is correct but geography is wrong → check egress independently.** An
application region label does not move the IP address. Confirm the proxy's configured
country and validate the observed egress with a public IP endpoint. If the application
also needs sticky sessions, retain the same authorized session while testing. Change
one variable at a time; simultaneously changing cookies, IP, and browser makes the
successful change impossible to identify.

## 4. Is the response usable content?

**200 with zero expected records → inspect before rotating.** Check the final
target URL, expected selector, content type, and rendering readiness. A legitimate
empty page or selector change can resemble a decoy. Body size is supporting context,
not a verdict. If the response URL belongs to a rendering API, resolve pagination
against the unwrapped target. Relative URLs joined against the transport host can
produce valid HTTP requests for entirely wrong resources.

**Verification widget → record a CAPTCHA hypothesis.** Reduce pressure and compare
a single controlled request. If evidence points to IP reputation, discuss an
authorized residential test and its cost with the operator. Browser-check prompts
instead suggest checking JavaScript execution and whether a supported unblocker
fits the integration. Neither recommendation guarantees access. The classifier
provides evidence and a proposed action; it does not solve challenges or switch
services automatically.

## 5. Did a dependency upgrade introduce it?

**Works on the old version → reproduce the smallest interface change.** Pin both
versions in separate environments, use the same offline fixture, and compare startup
errors and exported items. For spider output middleware, distinguish a synchronous
iterable from an asynchronous stream. The migration lab checks the real framework
on three pinned versions and verifies the item survives. A successful process exit
alone is insufficient evidence that a crawl produced data.

Close the ticket with the smallest verified fix, the exact reproduction command,
the observed result, and the remaining uncertainty. Keep the reproduction test:
it gives the next support engineer a cheaper starting point than the original incident.
