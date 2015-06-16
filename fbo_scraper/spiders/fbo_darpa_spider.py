################################################################################
#    Author: Greg Kramida (github id: Algomorph)
# Copyright: (2015) Gregory Kramida
#   License: Apache V2
#            [That means (basically): feel free to modify, sell, 
#             whatever, just do not remove the original author's credits/notice 
#             from this file. For details see LICENSE file.] 
################################################################################

#import scrapy
import scrapy.http
#import urllib
import re
import time
import random
from scrapy.selector import Selector
import htmlentitydefs

from fbo_scraper.items import Opportunity

class FboDarpaSpider(scrapy.Spider):
	name = "fbo_darpa"
	# this number is specific for DARPA.
	#  see value attribute of <input id="dnf_class_values_procurement_notice__agency_" ...>
	#  after you type & choose the name of the desired agency on the fbo.gov front page.
	agency_id = "048f413b4c64abc6c0afbc36b09f099d"
	# this name is specific for DARPA. It may be nonessential, I (Algomorph) have not checked.
	#  see value attribute of <input id="autocomplete_input_dnf_class_values_procurement_notice__agency_" ...>
	#  after you type & choose the name of the desired agency on the fbo.gov front page. 
	agency_autocomplete_name = "Other Defense Agencies/Defense Advanced Research Projects Agency"
	allowed_domains = ["www.fbo.gov"]
	index_url = "https://www.fbo.gov/index"
	# number of opportunities per page
	opportunities_per_page = 100
	
	# Constructor
	# synopsis_type may be: first_filled, complete
	def __init__(self, *args, **kwargs):
		self.data_params_determined = False
		random.seed()
		super(FboDarpaSpider, self).__init__(*args, **kwargs)
	
	
	start_url = index_url + "?s=opportunity&mode=list&tab=list&tabmode=list&pp=" + str(opportunities_per_page)
	
	def construct_list_query_request(self, url, callback):
		payload = {
			"dnf_class_values[procurement_notice][keywords]":"",
			"dnf_class_values[procurement_notice][_posted_date]":"",
			"dnf_class_values[procurement_notice][agency]":FboDarpaSpider.agency_id,
			"dnf_class_values[procurement_notice][zipstate]":"",
			"dnf_class_values[procurement_notice][procurement_type][]":"",
			"dnf_class_values[procurement_notice][set_aside][]":"",
			"dnf_class_values[procurement_notice][dnf_class_name]":"procurement_notice",
			"dnf_class_values[procurement_notice][notice_id]":"af741dd47e56d8a1b06c0a2788481f07",
			"dnf_class_values[procurement_notice][posted]":"" ,
			"autocomplete_input_dnf_class_values[procurement_notice][agency]":FboDarpaSpider.agency_autocomplete_name,
			"search_filters":"search",
			"_____dummy":"dnf_",
			"so_form_prefix":"dnf_",
			"dnf_opt_action":"search",
			"dnf_opt_template":"T9w/cGwAWbswybmDX7oTdTXxVYcDLoQW1MDkvvEnorFrm5k54q2OU09aaqzsSe6m",
			"dnf_opt_template_dir":"Yx BvwAhyFyVugII8bRnJLG6WrxuiBuGRpBBjyvqt1KAkN/anUTlMWIUZ8ga9kY",
			"dnf_opt_subform_template":"NxAoWjH6Mp1qhhsA i7/zGF719zd85B9",
			"dnf_opt_finalize":"0",
			"dnf_opt_mode":"update",
			"dnf_opt_target":"",
			"dnf_opt_validate":"1",
			"mode":"list"
		}
		headers = {
			"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"Accept-Encoding":"gzip, deflate",
			"Accept-Language":"en-US,en;q=0.8,gl;q=0.6,ru;q=0.4",
			"Cache-Control":"no-cache",
			"Connection":"keep-alive",
			"Host":"www.fbo.gov",
			"Origin":"https://www.fbo.gov",
			"Pragma":"no-cache",
			"Referer":"https://www.fbo.gov/",
			"User-Agent":"Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36"
		}
		return scrapy.http.FormRequest(url, callback=callback,
								method="POST", formdata=payload,
								headers=headers)
		
	# @override
	# called to construct requests from start url(s)
	def start_requests(self):
		yield self.construct_list_query_request(FboDarpaSpider.start_url, self.parse_initial_opportunities_list)
		
	def parse_initial_opportunities_list(self, response):
		print "\n\n=========== Parsing Initial Notice Listing Page ==============\n"
		pattern = re.compile(r"\d\s[-]\s\d\d?\d?\s(?:of)\s(\d+)")
		x_of_y_pages = str(response.xpath("//span[@class='lst-cnt']/text()")[0].extract())
		self.num_opportunities_found = num_ops = int(pattern.match(x_of_y_pages).group(1))
		ops_per_page = FboDarpaSpider.opportunities_per_page;
		# Number of result list pages to traverse after the initial query
		self.list_page_number = num_pages = num_ops / ops_per_page + int(num_ops % ops_per_page > 0)
		# tweak the base url to generate urls for each page of result listing
		base_url = FboDarpaSpider.start_url
		list_page_urls = [base_url + "&pageID=" + str(page_id) for page_id in range(1, num_pages + 1)]
		# generate new request list
		requests = [self.construct_list_query_request(url, self.parse_opportunities_list_page) for url in list_page_urls]
		#yield requests[0]
		for request in requests:
			yield request
		
	def construct_notice_request(self, url, callback):
		headers = {
			"Host": "www.fbo.gov",
			"Connection": "keep-alive",
			"Pragma": "no-cache",
			"Cache-Control": "no-cache",
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36",
			"Accept-Encoding": "gzip, deflate, sdch",
			"Accept-Language": "en-US,en;q=0.8,gl;q=0.6,ru;q=0.4"
		}
		return scrapy.http.Request(url, callback=callback,
								method="GET",
								headers=headers)
		
	def parse_opportunities_list_page(self, response):
		print "\n\n=========== Parsing Notice Listing Page =============="
		print "=========== From URL: " + response.url + "\n"
		
		notice_urls = response.xpath("//a[@class='lst-lnk-notice']/@href").extract()
		# prepend with index, and ensure we're using "Complete View" to get all synopsis details if necessary
		notice_urls = [FboDarpaSpider.index_url + str(url).replace("&_cview=0", "&_cview=1") for url in notice_urls]
		#print "Parsed notice URLS:"
		#print notice_urls
		#print "\n"
		requests = [self.construct_notice_request(url, self.parse_opportunity_notice) for url in notice_urls]
		for request in requests:
			yield request
	
	def parse_opportunity_notice(self, response):
		bad_date = False
		print "\n============== Parsing Single Notice ====================="
		print "============== From: " + response.url
		#=================== GET DEADLINE DATE=================================
		date_xpath = "//div[@id='dnf_class_values_procurement_notice__response_deadline__widget']/text()"
		full_date_string = response.xpath(date_xpath)[0].extract()
		
		date_pattern = r"(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s\d\d?,\s\d\d\d\d"
		proper_date_string_matches = response.xpath(date_xpath)[0].re(date_pattern)
		if(full_date_string.strip() == u"-"):
			#not a real date, assume contionous submision date, in which case skip this notice 
			return
		
		if(len(proper_date_string_matches) != 1 ):
			print "===> Bad deadline detected, \"" + repr(full_date_string) + "\". Attempting to use the Original Response Date field instead."
			deadline_date = None
			bad_date = True
		if(bad_date):
			date_xpath = "//div[@id='dnf_class_values_procurement_notice__original_response_deadline__widget']/text()"
			full_date_string = response.xpath(date_xpath)[0].extract()
			proper_date_string_matches = response.xpath(date_xpath)[0].re(date_pattern)
			#if(len(proper_date_string_matches) != 1 ):
				#raise RuntimeError("fbo_scraper: encountered unknown Deadline Date format. Got: " + repr(full_date_string))
		
		if(len(proper_date_string_matches) > 0):
			first_match = str(proper_date_string_matches[0].strip())
			try:
				#try 3-letter month
				deadline_date = time.strptime(first_match, "%b %d, %Y")
			except(ValueError):
				#try full month name
				deadline_date = time.strptime(first_match, "%B %d, %Y")
		
		#Use this to get formatted Month#/Day#/Year string
		#time.strftime("%m/%d/%Y",deadline_date)
		
		opp = Opportunity()
		if(deadline_date):
			date_string = time.strftime("%m/%d/%Y",deadline_date)
		else:
			date_string = repr(full_date_string)
		opp["deadline_date"] = date_string
		opp["opportunity_title"] = response.xpath("//div[@class='agency-header-w']/div/h2/text()")[0].extract()
		opp["sponsor_number"] = str(response.xpath("//div[@id='dnf_class_values_procurement_notice__solicitation_number__widget']/text()")[0].extract()).strip()
		opp["announcement_type"] = str(response.xpath("//div[@id='dnf_class_values_procurement_notice__procurement_type__widget']/text()")[0].extract().strip())
		opp["program_url"] = response.url
		
		#=============   process synopsis (this is tough)    ==================#
		opp["synopsis"] = u""
		full_desc = response.xpath("//div[@id='dnf_class_values_procurement_notice__description__widget']")[0].extract()
		
		#some <p> tags have formatting, or perhaps
		#some idiot hand-pasted an entry from another website / text document and did not remove the formatting
		#hence the complicated query
		desc_text_query = ("./body/div/text()|./body/div/p/text()|" #regular text & paragraphs
						+"./body/div/p/span/text()|./body/div/p/span/span/text()|" #some queer line spacing & kerning 
						+"/body/div/p/strong/text()|" #some bold text / headers
						+"./body/div/div/span[@class='added']/text()") #the dates entries were added
		sel = Selector(text=full_desc).xpath(desc_text_query).extract()
		
		newline = u'\n'
		if(len(sel) > 100): #crazy formatting! Collapse (don't insert newlines except for dates)
			entr_date_pattern = re.compile(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d\d?,\s\d\d\d\d\s\d\d?:\d\d?\d\s(?:pm|am)')
			sel = [entry.strip() + newline if entr_date_pattern.match(entry) or entry == u'Added:' else entry for entry in sel]
		else:
			#insert newlines for all entries
			#trim whitespace
			sel = [entry.strip() + newline for entry in sel]
			#get rid of newline for last entry
			sel[len(sel)-1] = sel[len(sel)-1].strip()
				
		desc_text = u''.join(sel)
		#convert html special characters to unicode
		try:
			desc_text = re.sub(r'&([^;]+);', lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), desc_text)
		except(KeyError):
			pass #ignore step
		
		desc_text = desc_text.strip()#remove trailing newlines
		
		opp["synopsis"] = desc_text
		
		#leave office blank for now
		opp["office"] = ""
		opp["hand_check_date"] = bad_date
		yield opp
