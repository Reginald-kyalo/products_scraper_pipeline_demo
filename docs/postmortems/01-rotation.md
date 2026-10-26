# 01 — Retries that amplified a temporary limit

**Context:** Synthetic offline support lab; no production incident is claimed.

**Symptom:** A practice downloader returned 429 twice before becoming available.
An immediate retry loop would spend the request budget without giving it time to recover.

**Wrong hypothesis:** Every unsuccessful response requires a new proxy, and rotating
alone is enough to repair the request.

**Proof:** A fake download handler supplies the exact sequence 429 → 429 → 200
through the real Scrapy engine. Unit tests separately capture the delay schedule:
1 second, then 2 seconds. They assert that the third response yields an item and
that a permanent failure stops after the retry budget. No network timing is inferred
from the fake responses.

**Fix:** Use one retry owner, rotate per request, wait without blocking the reactor,
respect capped server delays, and count outcomes by proxy slot. Clear copied proxy
authentication when switching slots. Leave programming errors visible instead of
retrying every exception.

**Verification:** `pytest tests/test_rotation.py -q` checks the sequence, final
failure, timeout recovery, direct mode, authentication handling, and redacted
scoreboard. The offline runner traverses Scrapy's actual downloader stack.

**Prevention:** Keep retries bounded and test the permanent-failure case. For
sustained limits, pause and reduce the overall rate. Rotation is one diagnostic
variable, not a substitute for managing request pressure.
