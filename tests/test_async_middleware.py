import json
import subprocess
import sys

import pytest
from async_middleware import AsyncTagMiddleware, LegacyTagMiddleware
from packaging.version import Version
from scrapy import Request, __version__
from scrapy.http import HtmlResponse


async def test_fixed_middleware_streams_items_and_preserves_requests():
    request = Request("https://books.toscrape.com/")

    async def items():
        yield {"title": "Example book"}
        yield request

    output = [
        item
        async for item in AsyncTagMiddleware().process_spider_output(
            HtmlResponse(request.url), items(), None
        )
    ]
    assert output == [{"title": "Example book", "demo_checked": True}, request]


async def test_first_item_not_buffered_before_upstream_failure():
    async def items():
        yield {"title": "Example book"}
        raise RuntimeError("synthetic downstream failure")

    stream = AsyncTagMiddleware().process_spider_output(None, items(), None)
    assert await anext(stream) == {"title": "Example book", "demo_checked": True}
    with pytest.raises(RuntimeError, match="synthetic downstream"):
        await anext(stream)


def test_legacy_reproducer_cannot_iterate_async_output():
    async def items():
        yield {"title": "Example book"}

    with pytest.raises(TypeError):
        list(LegacyTagMiddleware().process_spider_output(None, items(), None))


@pytest.mark.parametrize("legacy", [False, True])
def test_real_scrapy_engine_migration_contract(tmp_path, legacy):
    output = tmp_path / "items.json"
    command = [
        sys.executable,
        "05_async_middleware_scrapy213/demo.py",
        "--offline",
        "--output",
        str(output),
    ]
    if legacy:
        command.append("--legacy")
    process = subprocess.run(command, capture_output=True, text=True, timeout=30)
    supports_legacy = Version(__version__) < Version("2.16")
    if legacy and not supports_legacy:
        assert process.returncode != 0
        assert not output.exists()
        assert "process_spider_output" in process.stderr
    else:
        assert process.returncode == 0, process.stderr
        assert json.loads(output.read_text()) == [{"title": "Example book", "demo_checked": True}]
        if legacy and Version(__version__) >= Version("2.13"):
            assert "doesn" in process.stderr and "asynchronous" in process.stderr
