#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================
UPDATES :
- Rotating User-Agents & Proxies
- AutoThrottle & HTTP Caching
- Custom logging via Rich
- Robust error handling with errbacks
- Stats collection and signal handling
- Type hints and detailed docstrings
"""
import scrapy
import re
import json
import random
import logging
from typing import Any, Dict, List, Optional
from scrapy import signals
from scrapy.http import Request, Response
from scrapy.exceptions import CloseSpider
from datetime import datetime
import logger 


class AmazonSpider(scrapy.Spider):  
    """
    A feature-rich Scrapy spider for Amazon

    Attributes:
        name (str): Unique spider name
        allowed_domains (List[str]): Domains allowed to crawl
        keyword (str): Search keyword, override via -a keyword on CLI
        start_urls (List[str]): Initial search URL(s)
    """
    name: str = "amazon_supercharged"
    allowed_domains: List[str] = ["amazon.com"]
    keyword: str = getattr(scrapy.utils.project, 'keyword', 'laptops')
    start_urls: List[str] = [f"https://www.amazon.com/s?k={keyword}"]

    # Rotation lists
    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
        '(KHTML, like Gecko) Version/15.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0',
    ]
    PROXIES: List[str] = [
        # 'http://user:pass@proxy1:port',
        # 'http://proxy2:port',
    ]

    custom_settings: Dict[str, Any] = {
        # Enable AutoThrottle
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_DEBUG': False,
        # Enable HTTP caching
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 86400,
        # Concurrency & throttling
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 0.5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        # Retry & timeouts
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 5,
        'DOWNLOAD_TIMEOUT': 15,
        # Logging
        'LOG_LEVEL': 'DEBUG',
        # Pipelines & middlewares
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 300,
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
        },
        'ITEM_PIPELINES': {
            # 'myproject.pipelines.ValidationPipeline': 100,
            # 'myproject.pipelines.MongoPipeline': 300,
        },
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.start_time: datetime = datetime.utcnow()
        self.total_items: int = 0
        # Connect signals
        self.crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)
        logger.info(f"[🎬] Spider initialized at {self.start_time.isoformat()} UTC")

    def start_requests(self):  # type: ignore
        """
        Dispatch first requests with rotating User-Agent and optional proxy
        """
        for url in self.start_urls:
            headers = {'User-Agent': random.choice(self.USER_AGENTS)}
            meta: Dict[str, Any] = {}
            if self.PROXIES:
                meta['proxy'] = random.choice(self.PROXIES)
            logger.debug(f"[➡️] Scheduling search request: {url}")
            yield Request(url, headers=headers, meta=meta, callback=self.parse, errback=self.errback)

    def parse(self, response: Response) -> Optional[Request]:  # type: ignore
        """
        Handle search results: enqueue product page requests & paginate
        """
        logger.info(f"[🔍] Parsing search page: {response.url}")
        results = response.css('div[data-component-type="s-search-result"]')
        logger.debug(f"[📦] Found {len(results)} result blocks")

        for block in results:
            rel = block.css('h2 a::attr(href)').get()
            if not rel:
                continue
            prod_url = response.urljoin(rel)
            headers = {'User-Agent': random.choice(self.USER_AGENTS)}
            meta = {'referer': response.url}
            logger.debug(f"[✉️] Queueing product: {prod_url}")
            yield Request(prod_url, headers=headers, meta=meta,
                          callback=self.parse_product, errback=self.errback)

        # Pagination
        next_page = response.css('ul.a-pagination li.a-last a::attr(href)').get()
        if next_page:
            next_url = response.urljoin(next_page)
            logger.info(f"[▶️] Next page → {next_url}")
            yield Request(next_url, headers={'User-Agent': random.choice(self.USER_AGENTS)},
                          callback=self.parse, errback=self.errback)
        return None

    def parse_product(self, response: Response) -> Dict[str, Any]:  # type: ignore
        """
        Extract detailed product information
        """
        logger.info(f"[💎] Scraping product page: {response.url}")
        def extract(query: str) -> str:
            return response.xpath(query).get(default='').strip()

        asin_match = re.search(r'/dp/([A-Z0-9]{10})', response.url)
        asin = asin_match.group(1) if asin_match else extract('//th[text()="ASIN"]/following-sibling::td/text()')
        title = extract('//span[@id="productTitle"]/text()')
        price = extract('//*[contains(@id,"priceblock_")]/text()')
        rating = extract('//span[@data-hook="rating-out-of-text"]/text()')
        reviews = extract('//span[@id="acrCustomerReviewText"]/text()')
        features = response.css('#feature-bullets .a-list-item::text').getall()
        features = [f.strip() for f in features if f.strip()]
        desc = extract('//div[@id="productDescription"]//p/text()')
        imgs: List[str] = []
        js_raw = response.xpath('//script[contains(.,"ImageBlockATF")]/text()').re_first(r'"colorImages":(\{.*?\})')
        if js_raw:
            try:
                data = json.loads(js_raw)
                imgs = [i['large'] for i in data.get('initial', [])]
            except Exception:
                imgs = []

        item: Dict[str, Any] = {
            'asin': asin,
            'title': title,
            'price': price,
            'rating': rating,
            'reviews': reviews,
            'features': features,
            'description': desc,
            'images': imgs,
            'url': response.url,
        }
        self.total_items += 1
        logger.success(f"[🏆] Parsed item #{self.total_items}: ASIN={asin} | Price={price}")
        return item

    def errback(self, failure: Any) -> None:  # type: ignore
        """
        Handle request errors
        """
        logger.error(f"[❌] Request failed: {failure.request.url}")  # noqa

    def spider_closed(self, spider: scrapy.Spider) -> None:  # type: ignore
        """
        Triggered when spider finishes
        """
        duration = datetime.utcnow() - self.start_time
        logger.info(f"[⏲️] Spider closed: duration={duration}, items_scraped={self.total_items}")
        if self.total_items == 0:
            raise CloseSpider("No items scraped — stopping spider")
