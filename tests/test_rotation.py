import logging

import pytest
from rotation import RotatingProxyMiddleware
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.settings import Settings
from twisted.internet.error import TimeoutError


@pytest.fixture
def waits():
    return []


@pytest.fixture
def middleware(waits):
    async def wait(seconds):
        waits.append(seconds)

    return RotatingProxyMiddleware(
        ["http://first.example:8080", "http://second.example:8080"],
        max_retries=2,
        base_delay=1,
        max_delay=8,
        wait=wait,
    )


def response(request, status=200, body=b"<html>Practice catalogue</html>", headers=None):
    return HtmlResponse(
        request.url, request=request, status=status, body=body, encoding="utf-8", headers=headers
    )


async def test_two_bans_then_success_rotates_and_backs_off(middleware, waits):
    request = Request("https://books.toscrape.com/")
    slots = []
    for status in (429, 429, 200):
        await middleware.process_request(request)
        slots.append(request.meta["proxy"])
        result = middleware.process_response(request, response(request, status))
        if status != 200:
            assert isinstance(result, Request)
            assert result.dont_filter
            request = result
        else:
            assert result.status == 200
    assert slots == [
        "http://first.example:8080",
        "http://second.example:8080",
        "http://first.example:8080",
    ]
    assert waits == [1, 2]
    assert middleware.health == [
        {"successes": 1, "bans": 1, "errors": 0},
        {"successes": 0, "bans": 1, "errors": 0},
    ]


async def test_retry_budget_returns_final_response(middleware):
    request = Request("https://books.toscrape.com/")
    for _ in range(2):
        await middleware.process_request(request)
        request = middleware.process_response(request, response(request, 403))
    await middleware.process_request(request)
    final = response(request, 403)
    assert middleware.process_response(request, final) is final


async def test_body_challenge_detected_and_auth_not_carried_to_new_proxy(middleware):
    request = Request("https://books.toscrape.com/")
    await middleware.process_request(request)
    request.headers["Proxy-Authorization"] = "Basic synthetic"
    retry = middleware.process_response(
        request, response(request, body=b"<html>Please verify you are human</html>")
    )
    await middleware.process_request(retry)
    assert retry.meta["proxy"] == "http://second.example:8080"
    assert b"Proxy-Authorization" not in retry.headers


@pytest.mark.parametrize("seconds", [3, 8])
async def test_retry_after_within_limit_is_respected(middleware, waits, seconds):
    request = Request("https://books.toscrape.com/")
    await middleware.process_request(request)
    retry = middleware.process_response(
        request, response(request, 429, headers={"Retry-After": str(seconds)})
    )
    await middleware.process_request(retry)
    assert waits == [seconds]


@pytest.mark.parametrize("header", ["90", "Wed, 01 Jan 2098 00:00:00 GMT"])
async def test_retry_after_over_limit_stops_retries(middleware, waits, caplog, header):
    request = Request("https://books.toscrape.com/")
    await middleware.process_request(request)
    final = response(request, 429, headers={"Retry-After": header})
    with caplog.at_level(logging.WARNING):
        result = middleware.process_response(request, final)
    assert result is final
    assert waits == []
    assert "pause the crawl" in caplog.text
    assert request.url not in caplog.text


async def test_transport_timeout_retried_but_programming_error_not_swallowed(middleware):
    request = Request("https://books.toscrape.com/")
    await middleware.process_request(request)
    assert middleware.process_exception(request, ValueError("bug")) is None
    retry = middleware.process_exception(request, TimeoutError())
    assert isinstance(retry, Request)
    assert middleware.health[0]["errors"] == 1


async def test_direct_mode_does_not_claim_proxy_rotation(waits):
    middleware = RotatingProxyMiddleware([])
    request = Request("https://books.toscrape.com/")
    await middleware.process_request(request)
    assert "proxy" not in request.meta
    assert isinstance(middleware.process_response(request, response(request, 503)), Request)


async def test_dont_retry_is_honored(middleware):
    request = Request("https://books.toscrape.com/", meta={"dont_retry": True})
    await middleware.process_request(request)
    final = response(request, 429)
    assert middleware.process_response(request, final) is final


def test_scoreboard_does_not_log_proxy_addresses(caplog):
    middleware = RotatingProxyMiddleware(["http://user:password@private.example:8080"])
    with caplog.at_level(logging.INFO):
        middleware.spider_closed(None)
    assert "slot=0" in caplog.text
    assert "private.example" not in caplog.text
    assert "password" not in caplog.text


def test_settings_reject_invalid_proxy_without_echoing_it(monkeypatch):
    monkeypatch.setenv("DEMO_PROXY_URLS", "socks5://secret.example:8080")
    from types import SimpleNamespace

    with pytest.raises(ValueError, match="HTTP") as error:
        RotatingProxyMiddleware.from_crawler(SimpleNamespace(settings=Settings()))
    assert "secret.example" not in str(error.value)


def test_offline_crawl_exercises_real_downloader_stack(tmp_path):
    import json
    import subprocess
    import sys

    output = tmp_path / "items.json"
    process = subprocess.run(
        [sys.executable, "01_proxy_rotation_scrapy/demo.py", "--offline", "--output", str(output)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(output.read_text()) == [{"title": "Example book"}]
    assert "bans=2" in process.stderr
