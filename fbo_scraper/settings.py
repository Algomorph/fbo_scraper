# -*- coding: utf-8 -*-
#from scrapy.settings.default_settings import DOWNLOAD_DELAY

# Scrapy settings for fbo_scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'fbo_scraper'

SPIDER_MODULES = ['fbo_scraper.spiders']
NEWSPIDER_MODULE = 'fbo_scraper.spiders'

ROBOTSTXT_OBEY = True
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY = 5.0

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# !!! ATTENTION: PLEASE REPLACE WITH YOUR OWN WEBSITE IF YOU ARE GOING TO USE USER_AGENT!
#USER_AGENT = 'fbo_scraper (+http://research.umd.edu/)'
