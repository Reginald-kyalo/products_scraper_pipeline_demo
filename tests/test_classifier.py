import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from classifier import classify

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("status", "fixture", "count", "kind", "action"),
    [
        (200, "books.html", 1, "ok", "continue"),
        (200, "captcha.html", 0, "captcha", "consider_residential"),
        (503, "challenge.html", 0, "js-challenge", "consider_unblocker"),
        (429, "captcha.html", 0, "rate-limited", "slow_down"),
        (200, "empty.html", 0, "decoy-empty", "inspect_then_rotate"),
    ],
)
def test_classifies_status_dom_and_expected_content(status, fixture, count, kind, action):
    result = classify(status, (FIXTURES / fixture).read_text(), count)
    assert result.kind == kind
    assert result.recommendation == action
    assert result.evidence


def test_empty_requires_known_expected_content():
    assert classify(200, "<html></html>", None).kind == "unknown"
    assert classify(200, "<html>" + "x" * 5000 + "</html>", 0).kind == "decoy-empty"


def test_captcha_word_in_article_does_not_claim_challenge():
    assert classify(200, "<article>A book about captcha systems</article>", 1).kind == "ok"


def test_error_response_not_misclassified_as_healthy():
    assert classify(500, "<html>Example error</html>", 1).kind == "unknown"
    assert classify(403, "<html>Access denied</html>", 0).recommendation == "inspect_then_rotate"


def test_browser_adapter_with_real_offline_dom(tmp_path):
    # Opt in only when Chromium has been installed; still no public network.
    if os.environ.get("DEMO_BROWSER_TEST") != "1":
        pytest.skip("Set DEMO_BROWSER_TEST=1 after playwright install chromium")
    output = tmp_path / "classification.json"
    result = subprocess.run(
        [
            sys.executable,
            "04_playwright_captcha_detect/classifier.py",
            "--fixture",
            str(FIXTURES / "books.html"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())["kind"] == "ok"


def test_content_with_newsletter_widget_does_not_recommend_proxy_escalation():
    result = classify(
        200, '<article>Example book</article><form><div class="g-recaptcha"></div></form>', 1
    )
    assert result.kind == "unknown"
    assert result.recommendation == "inspect"


def test_hidden_and_script_prompts_do_not_claim_browser_challenge():
    html = (
        '<article>Example book</article><script>"checking your browser"</script>'
        "<div hidden>Please verify you are human</div>"
    )
    assert classify(200, html, 1).kind == "ok"
