# Amazon Scrapy Spider

A robust, feature-rich Scrapy crawler designed to extract detailed product information from Amazon search results. This project demonstrates advanced Scrapy techniques, including User-Agent rotation, proxy support, AutoThrottle, HTTP caching, error handling, and custom logging (Rich integration).

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Spider Architecture](#spider-architecture)
7. [Selectors & Extraction Logic](#selectors--extraction-logic)
8. [Error Handling & Retries](#error-handling--retries)
9. [Output & Integration](#output--integration)
10. [Extending & Customization](#extending--customization)
11. [License](#license)

---

## Features

* **Search Pagination**: Automatically follows “Next” links to crawl multiple pages.
* **User-Agent Rotation**: Randomizes User-Agent headers to minimize blocking.
* **(Optional) Proxy Support**: Configurable proxy list for request routing.
* **AutoThrottle & HTTP Cache**: Politeness controls with dynamic throttling and cached responses.
* **Error Handling**: Built-in retry logic and `errback` callbacks for robustness.
* **Signal Hooks**: Tracks start and close events to log crawl duration and item counts.
* **Structured Output**: Yields JSON/dict items with standardized fields for downstream processing.

---

## Prerequisites

* **Python 3.8+**
* **Scrapy 2.5+**
* **Rich** (optional, for colored logging)
* **Git** (for version control)

---


## Configuration

* **Search Keyword**: Pass `-a keyword=<term>` to override default search term (e.g., `scrapy crawl amazonScraper -a keyword=laptops`).
* **Proxies**: Edit the `PROXIES` list in `amazon_spider_supercharged.py` to include your HTTP/HTTPS proxy endpoints.
* **Throttle Settings**: Adjust AutoThrottle and `DOWNLOAD_DELAY` values in `custom_settings` as needed.

---

## Usage

* **Run the spider**:

  ```bash
  scrapy crawl amazonScraper -o output.json
  ```

  Output formats supported: `JSON`, `CSV`, `XML` (via Scrapy’s `-o` flag).

* **Examples**:

  * Export CSV:  `scrapy crawl amazonScraper -a keyword=headphones -o headphones.csv`
  * Limit depth:  `scrapy crawl amazonScraper --depth-limit 3`

---

## Spider Architecture

1. **`start_requests`**: Initializes requests with random User-Agent and optional proxy.
2. **`parse`**: Handles search-results page, extracts product links, and enqueues pagination.
3. **`parse_product`**: Scrapes individual product pages, extracting:

   * ASIN
   * Title
   * Price
   * Rating & Review count
   * Feature bullets & Description
   * Image URLs
4. **`errback`**: Catches request failures and logs errors for review.
5. **`spider_closed`**: Computes crawl duration and total items scraped.

---

## Selectors & Extraction Logic

| Field         | Selector/XPath                                   | Notes                         |
| ------------- | ------------------------------------------------ | ----------------------------- |
| `asin`        | `re.search(r"/dp/([A-Z0-9]{10})", response.url)` | Fallback to table lookup      |
| `title`       | `//span[@id="productTitle"]/text()`              | Stripped whitespace           |
| `price`       | `//*[contains(@id,"priceblock_")]/text()`        | Handles multiple price blocks |
| `rating`      | `//span[@data-hook="rating-out-of-text"]/text()` | e.g. “4.5 out of 5 stars”     |
| `reviews`     | `//span[@id="acrCustomerReviewText"]/text()`     | e.g. “1,234 ratings”          |
| `features`    | `#feature-bullets .a-list-item::text`            | Cleans empty items            |
| `description` | `//div[@id="productDescription"]//p/text()`      | Optional long text block      |
| `images`      | JSON block in `<script>` tagged `ImageBlockATF`  | Parses `colorImages.initial`  |

---

## Error Handling & Retries

* **`RETRY_ENABLED`** and **`RETRY_TIMES`** ensure transient failures are retried.
* **`DOWNLOAD_TIMEOUT`** catches hung requests.
* **`errback`** logs any failed URL for manual inspection.

---

## Output & Integration

* Items yield Python dicts with consistent schema; pipe to JSON/CSV:

  ```bash
  scrapy crawl amazonScraper -o products.json
  ```
* Integrate in pipelines (e.g., validation, database insertion) by adding to `ITEM_PIPELINES`.

---

## Extending & Customization

* **Add new fields**: Extend `parse_product` with additional selectors or API calls.
* **Alternate output**: Implement custom `Item` classes and exporters.
* **Distributed crawling**: Integrate with Scrapyd or Frontera for large-scale scraping.

---

## License

MIT License © Your Name

---

*Happy scraping!*
