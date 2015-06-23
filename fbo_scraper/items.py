# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class Opportunity(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    opportunity_title = scrapy.Field()
    sponsor_number = scrapy.Field(serializer=str)
    announcement_type = scrapy.Field()
    synopsis = scrapy.Field()
    program_url = scrapy.Field()
    office = scrapy.Field(serializer=str)
    deadline_date = scrapy.Field(serializer=str)
    check_date = scrapy.Field(serializer=bool)
    check_office = scrapy.Field(serializer=bool)
    check_office_wide = scrapy.Field(serializer=bool)
