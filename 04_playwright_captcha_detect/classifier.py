"""Inspect a page once; emit triage advice, never solve a challenge or auto-retry."""

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from parsel import Selector


@dataclass(frozen=True)
class Classification:
    kind: str
    recommendation: str
    evidence: tuple[str, ...]


def classify(status: int, html: str, expected_count: int | None = None) -> Classification:
    dom = Selector(text=html)
    text = " ".join(
        dom.xpath(
            "//text()[not(ancestor::script or ancestor::style or ancestor::template "
            "or ancestor::*[@hidden or @aria-hidden='true'])]"
        ).getall()
    ).lower()
    if status == 429:
        return Classification("rate-limited", "slow_down", ("HTTP 429",))
    widget = dom.css('.g-recaptcha, .h-captcha, iframe[src*="recaptcha"]').xpath(
        "self::*[not(ancestor-or-self::*[@hidden or @aria-hidden='true'])]"
    )
    captcha = bool(widget) or any(
        phrase in text for phrase in ("verify you are human", "complete the captcha")
    )
    challenge = any(
        phrase in text for phrase in ("checking your browser", "enable javascript to continue")
    )
    if (
        200 <= status < 300
        and expected_count is not None
        and expected_count > 0
        and (captcha or challenge)
    ):
        return Classification(
            "unknown", "inspect", ("expected content and verification signals both present",)
        )
    if captcha:
        return Classification("captcha", "consider_residential", ("verification DOM or prompt",))
    if challenge:
        return Classification("js-challenge", "consider_unblocker", ("browser challenge prompt",))
    if status == 403:
        return Classification("unknown", "inspect_then_rotate", ("HTTP 403; inspect policy first",))
    if 200 <= status < 300 and expected_count == 0:
        return Classification(
            "decoy-empty",
            "inspect_then_rotate",
            (
                "expected content absent",
                f"snapshot bytes={len(html.encode())}",
                "suspected empty shell; legitimate emptiness remains possible",
            ),
        )
    if 200 <= status < 300 and expected_count is not None and expected_count > 0:
        return Classification("ok", "continue", ("expected content present",))
    return Classification("unknown", "inspect", ("insufficient evidence",))


async def inspect_page(url=None, fixture=None, selector="article.product_pod", status=200):
    from playwright.async_api import async_playwright

    async with async_playwright() as driver:
        browser = await driver.chromium.launch()
        try:
            page = await browser.new_page()
            if fixture:
                # Synthetic fixtures cannot make subresource network requests.
                await page.route("**/*", lambda route: route.abort())
                await page.set_content(Path(fixture).read_text(), wait_until="domcontentloaded")
            else:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                status = response.status if response else 0
            count = await page.locator(selector).count() if selector else None
            return classify(status, await page.content(), count)
        finally:
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--url",
        choices=[
            "https://books.toscrape.com/",
            "https://quotes.toscrape.com/",
        ],
        default=None,
    )
    source.add_argument("--fixture", type=Path)
    parser.add_argument("--selector", default="article.product_pod")
    parser.add_argument("--status", type=int, default=200, help="Synthetic fixture status only")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(
        inspect_page(
            url=args.url or "https://books.toscrape.com/",
            fixture=args.fixture,
            selector=args.selector,
            status=args.status,
        )
    )
    report = json.dumps(asdict(result), indent=2)
    if args.output:
        args.output.write_text(report + "\n")
    else:
        print(report)


if __name__ == "__main__":
    main()
