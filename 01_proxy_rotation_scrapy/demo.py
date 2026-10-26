"""One-page practice crawl; --offline injects two bans then a successful response."""

import argparse
import os
import sys
from pathlib import Path

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse
from twisted.internet.defer import succeed


class FixtureDownloadHandler:
    lazy = True

    def __init__(self):
        self.calls = 0

    def download_request(self, request, spider=None):
        self.calls += 1
        html = '<article class="product_pod"><h3><a title="Example book">Book</a></h3></article>'
        return succeed(
            HtmlResponse(
                request.url,
                request=request,
                status=429 if self.calls <= 2 else 200,
                body=html.encode(),
                encoding="utf-8",
            )
        )

    def close(self):
        pass


class PracticeSpider(scrapy.Spider):
    name = "rotation_practice"
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        for title in response.css("article.product_pod h3 a::attr(title)").getall():
            yield {"title": title}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("/tmp/rotation-demo-items.json"))
    args = parser.parse_args()
    settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "rotation.RotatingProxyMiddleware": 610,
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
        },
        "ROBOTSTXT_OBEY": True,
        "TELNETCONSOLE_ENABLED": False,
        "DOWNLOAD_DELAY": 1,
        "DOWNLOAD_TIMEOUT": 15,
        "CONCURRENT_REQUESTS": 1,
        "FEEDS": {str(args.output.resolve()): {"format": "json", "overwrite": True}},
        "LOG_LEVEL": "INFO",
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "WARN_ON_GENERATOR_RETURN_VALUE": False,
    }
    if args.offline:
        os.environ["DEMO_PROXY_URLS"] = "http://offline.example:8080"
        settings.update(
            {
                "DOWNLOAD_HANDLERS": {"https": "demo.FixtureDownloadHandler"},
                "ROBOTSTXT_OBEY": False,
                "DOWNLOAD_DELAY": 0,
                "DEMO_BASE_DELAY": 0.01,
            }
        )
    process = CrawlerProcess(settings)
    crawler = process.create_crawler(PracticeSpider)
    failures = []
    pending = process.crawl(crawler)
    pending.addErrback(lambda failure: failures.append(failure))
    process.start()
    for failure in failures:
        print(failure.getErrorMessage(), file=sys.stderr)
    if failures or crawler.stats.get_value("item_scraped_count", 0) < 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
