"""A sync-only reproducer and its streaming async replacement."""


class LegacyTagMiddleware:
    """Intentionally incompatible with async iterators and Scrapy 2.16+."""

    def process_spider_output(self, response, result, spider=None):
        for item in result:
            if isinstance(item, dict):
                item = {**item, "demo_checked": True}
            yield item


class AsyncTagMiddleware:
    """Supported on every version in the demo's 2.12 / 2.13 / 2.16 matrix."""

    async def process_spider_output(self, response, result, spider=None):
        async for item in result:
            if isinstance(item, dict):
                item = {**item, "demo_checked": True}
            yield item
