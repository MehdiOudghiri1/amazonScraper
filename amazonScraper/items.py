# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

import scrapy

class AmazonItem(scrapy.Item):
    """
    Item definition for Amazon product details.
    Fields correspond to data extracted by the AmazonSpider.
    """
    asin = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    rating = scrapy.Field()
    reviews = scrapy.Field()
    features = scrapy.Field()
    description = scrapy.Field()
    images = scrapy.Field()
    url = scrapy.Field()

