"""Bounded retries and per-slot accounting; no provider-specific configuration."""

import logging
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from scrapy import signals
from scrapy.utils.defer import maybe_deferred_to_future
from twisted.internet.error import ConnectError, DNSLookupError, TCPTimedOutError, TimeoutError
from twisted.internet.task import deferLater

logger = logging.getLogger(__name__)


async def reactor_wait(seconds):
    # Import after Scrapy selects the reactor. Never block the event loop with sleep().
    from twisted.internet import reactor

    await maybe_deferred_to_future(deferLater(reactor, seconds, lambda: None))


class RotatingProxyMiddleware:
    def __init__(self, proxies, max_retries=2, base_delay=1, max_delay=30, wait=reactor_wait):
        self.proxies = list(proxies)
        for proxy in self.proxies:
            parsed = urlsplit(proxy)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("Proxy entries must be absolute HTTP(S) URLs")
        if max_retries < 0 or base_delay < 0 or max_delay < base_delay:
            raise ValueError("Retry budget and delays must be nonnegative and bounded")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.wait = wait
        self.cursor = 0
        self.health = [dict(successes=0, bans=0, errors=0) for _ in self.proxies]

    @classmethod
    def from_crawler(cls, crawler):
        instance = cls(
            [p.strip() for p in os.environ.get("DEMO_PROXY_URLS", "").split(",") if p.strip()],
            max_retries=crawler.settings.getint("DEMO_MAX_RETRIES", 2),
            base_delay=crawler.settings.getfloat("DEMO_BASE_DELAY", 1),
            max_delay=crawler.settings.getfloat("DEMO_MAX_DELAY", 30),
        )
        crawler.signals.connect(instance.spider_closed, signal=signals.spider_closed)
        return instance

    async def process_request(self, request, spider=None):
        delay = request.meta.pop("demo_delay", 0)
        if delay:
            await self.wait(delay)
        if self.proxies:
            slot = self.cursor % len(self.proxies)
            self.cursor += 1
            # A copied retry must not reuse authentication from a different proxy.
            request.headers.pop("Proxy-Authorization", None)
            request.meta["proxy"] = self.proxies[slot]
            request.meta["demo_proxy_slot"] = slot

    def _count(self, request, event):
        slot = request.meta.get("demo_proxy_slot")
        if slot is not None:
            self.health[slot][event] += 1

    def _retry(self, request, retry_after=0):
        attempts = request.meta.get("demo_retries", 0)
        if request.meta.get("dont_retry") or attempts >= self.max_retries:
            return None
        retry = request.copy()
        retry.dont_filter = True
        retry.meta["demo_retries"] = attempts + 1
        retry.meta["demo_delay"] = min(
            self.max_delay,
            max(retry_after, self.base_delay * 2**attempts),
        )
        return retry

    def process_response(self, request, response, spider=None):
        body = response.body[:65536].lower()
        banned = response.status in {403, 429, 503} or any(
            signal in body for signal in (b"verify you are human", b"checking your browser")
        )
        if not banned:
            if 200 <= response.status < 300:
                self._count(request, "successes")
            return response
        self._count(request, "bans")
        retry_after = self._retry_after(response.headers.get("Retry-After", b""))
        return self._retry(request, retry_after) or response

    def process_exception(self, request, exception, spider=None):
        if isinstance(exception, (ConnectError, DNSLookupError, TimeoutError, TCPTimedOutError)):
            self._count(request, "errors")
            return self._retry(request)
        return None

    @staticmethod
    def _retry_after(raw):
        try:
            return max(0, float(raw))
        except ValueError:
            try:
                return max(
                    0,
                    (
                        parsedate_to_datetime(raw.decode()) - datetime.now(timezone.utc)
                    ).total_seconds(),
                )
            except (ValueError, TypeError, OverflowError):
                return 0

    def spider_closed(self, spider, reason=None):
        for slot, counts in enumerate(self.health):
            logger.info(
                "Proxy health slot=%d successes=%d bans=%d errors=%d",
                slot,
                counts["successes"],
                counts["bans"],
                counts["errors"],
            )
