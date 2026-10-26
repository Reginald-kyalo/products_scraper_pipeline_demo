"""Run the before/after example through the real Scrapy engine."""

import argparse
import sys
from pathlib import Path
from urllib.parse import quote

import scrapy
from scrapy.crawler import CrawlerProcess


class PracticeSpider(scrapy.Spider):
    name = "async_practice"
    start_urls = ["https://books.toscrape.com/"]

    async def parse(self, response):
        for title in response.css("article.product_pod h3 a::attr(title)").getall():
            yield {"title": title}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--legacy", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("/tmp/async-demo-items.json"))
    args = parser.parse_args()
    middleware = "LegacyTagMiddleware" if args.legacy else "AsyncTagMiddleware"
    settings = {
        "SPIDER_MIDDLEWARES": {f"async_middleware.{middleware}": 543},
        "FEEDS": {str(args.output.resolve()): {"format": "json", "overwrite": True}},
        "LOG_LEVEL": "WARNING",
        "TELNETCONSOLE_ENABLED": False,
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1,
        "DOWNLOAD_TIMEOUT": 15,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "WARN_ON_GENERATOR_RETURN_VALUE": False,
    }
    process = CrawlerProcess(settings)
    crawler = process.create_crawler(PracticeSpider)
    start_urls = PracticeSpider.start_urls
    if args.offline:
        html = '<article class="product_pod"><h3><a title="Example book">Book</a></h3></article>'
        start_urls = ["data:text/html," + quote(html)]
    failures = []
    pending = process.crawl(crawler, start_urls=start_urls)
    pending.addErrback(lambda failure: failures.append(failure))
    process.start()
    for failure in failures:
        print(failure.getErrorMessage(), file=sys.stderr)
    if failures or crawler.stats.get_value("item_scraped_count", 0) < 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
