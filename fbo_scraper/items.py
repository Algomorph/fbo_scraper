# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy



class FboScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
	opportunity_title = scrapy.Field()
	office = scrapy.Field()
	sponsor_number = scrapy.Field()
	deadline_date = scrapy.Field()
	announcement_type = scrapy.Field()
	synopsys = scrapy.Field()
	program_url = scrapy.Field()
