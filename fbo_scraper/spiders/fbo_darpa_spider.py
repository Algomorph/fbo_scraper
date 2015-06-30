################################################################################
#    Author: Greg Kramida (github id: Algomorph)
# Copyright: (2015) Gregory Kramida
#   License: Apache V2
#            [That means (basically): feel free to modify, sell, 
#             whatever, just do not remove the original author's credits/notice 
#             from the files. For details, see LICENSE file.] 
################################################################################

import scrapy.http
import re
import time
import random
from scrapy.selector import Selector
import htmlentitydefs

from fbo_scraper.items import Opportunity
from fbo_scraper.db.pdexcel import PandasExcelHelper

class FboDarpaSpider(scrapy.Spider):
	'''
	A utility for scraping DARPA notices from the fbo.gov website
	Run from root directory (top-level fbo_scraper folder) like this:
		scrapy crawl fbo_darpa
	'''
	#spider's name (for scrapy)
	name = "fbo_darpa"
	
	# this number is specific for DARPA.
	#  see value attribute of <input id="dnf_class_values_procurement_notice__agency_" ...>
	#  after you type & choose the name of the desired agency on the fbo.gov front page.
	agency_id = "048f413b4c64abc6c0afbc36b09f099d"
	
	# this name is specific for DARPA. It may be nonessential, I (Algomorph) have not checked.
	#  see value attribute of <input id="autocomplete_input_dnf_class_values_procurement_notice__agency_" ...>
	#  after you type & choose the name of the desired agency on the fbo.gov front page. 
	agency_autocomplete_name = "Other Defense Agencies/Defense Advanced Research Projects Agency"
	allowed_domains = ["www.fbo.gov", "www.darpa.mil"]
	
	# number of opportunities per page for the fbo.gov website
	opportunities_per_page = 100
	fbo_index_url = "https://www.fbo.gov/index"
	fbo_start_url = fbo_index_url + "?s=opportunity&mode=list&tab=list&tabmode=list&pp=" + str(opportunities_per_page)
	
	darpa_index_url = "http://www.darpa.mil"
	darpa_start_url = darpa_index_url + "/work-with-us/opportunities?ppl=viewall&PP=0"
	
	# these are "expected" not to change in the next 50 years
	darpa_office_by_acronym = {
		"BTO":"Biological Technologies Office",
		"DSO":"Defense Sciences Office",
		"I2O":"Information Innovation Office",
		"MTO":"Microsystems Technology Office",
		"STO":"Strategic Technologies Office",
		"TTO":"Tactical Technology Office"
	}
	
	
	def __init__(self, dont_skip_continuous="false", dont_skip_office_wide="false", *args, **kwargs):
		'''
		Constructor
		@param dont_filter_continous whether or not to skip notices with continuous 
		                            submission dates. Set to "true" or "false".
		@type dont_filter_continous String
		@param dont_filter_office_wide whether or not to skip notices with "Office-Wide"
									 (or some form thereof) in the title. Set to
									 "true" or "false".
		'''
		self.data_params_determined = False
		
		if(dont_skip_continuous in ["true", "yes", "y", "Y"]):
			self.dont_filter_continous = True
		else:
			self.dont_filter_continous = False
			
		if(dont_skip_office_wide in ["true", "yes", "y", "Y"]):
			self.dont_filter_office_wide = True
		else:
			self.dont_filter_office_wide = False
			
		# a dictionary of DARPA announcements, keyed by opportunity_title, 
		# containing office of each as scraped from the darpa.mil website
		self.darpa_announcement_dict = {}
			
		# seed the random generator
		random.seed()
		
		# preload the existing notices, so that we may avoid scraping them
		#self.db = PandasExcelHelper()
		super(FboDarpaSpider, self).__init__(*args, **kwargs)
	
	def start_requests(self):
		'''	
		@override
		called to construct requests from start url(s)
		'''
		yield self.start_darpa_scraping()
	
	def construct_fbo_list_query_request(self, url, callback):
		'''
		build a FBO list page query based on the passed-in URL
		'''
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

	def start_darpa_scraping(self):
		'''
		start scraping the office from the announcements on the darpa.mil hash, 
		and storing them in a local dictionary
		'''
		return scrapy.http.FormRequest(FboDarpaSpider.darpa_start_url, callback=self.parse_darpa_website_announcement_list,
									method="GET")
	
	
	def parse_darpa_website_announcement_list(self, response):
		'''
		parse the list of announcements from the darpa website to get the office & the next list page
		'''
		print "\n\n=========== Parsing darpa.mil Announcement Listing Page ==============\n"
		print "=========== From URL: " + response.url + "\n"
		# process the titles and offices
		titles = [str(unicode_title.strip()) for unicode_title 
				in response.xpath("//h2[@class='listing__link']/a/text()").extract()]
		office_acronyms = [str(unicode_office.strip()) for unicode_office 
						in response.xpath("//div[@class='listing__office']/text()").extract()]
		offices = [FboDarpaSpider.darpa_office_by_acronym[office_acronym] for office_acronym in office_acronyms]
		
		# if the total #-s are not the same, something is wrong here.
		if(len(offices) != len(titles)):
			raise RuntimeError("The number of announcement titles (" + str(len(titles)) + 
							") does not correspond to the number of announcement offices ("
							+ str(len(offices)) + 
							") on the darpa.mil page!")
		
		for ix_announcement in xrange(len(titles)):
			self.darpa_announcement_dict[titles[ix_announcement]] = offices[ix_announcement]
		
		# pattern for getting page numbers (0-based) from a darpa listing url
		page_num_pattern = re.compile(r"(?:http:\/\/www\.darpa\.mil)?\/work-with-us\/opportunities\?ppl=viewall&PP=(\d+)")
		
		# determine which listing page we are on right now
		page_num = int(page_num_pattern.match(response.url).groups(0)[0])
		
		# get the Page 1, 2, 3, ..., Last urls at the bottom of the page
		page_urls = [str(url) for url in response.xpath("//div[@class='pager']/ul/li/a/@href")[:-1].extract()]
		next_darpa_url = None
		
		# determine where to go next
		for page_url in page_urls:
			url_leads_to_page = int(page_num_pattern.match(page_url).groups(0)[0])
			if(url_leads_to_page <= page_num):
				continue
			next_darpa_url = FboDarpaSpider.darpa_index_url + page_url
		if(next_darpa_url):
			# still have more darpa.mil list pages to go through
			yield scrapy.http.FormRequest(next_darpa_url, callback=self.parse_darpa_website_announcement_list,
									method="GET")
		else:
			# done with darpa listing, get stuff from fbo.gov now
			yield self.start_fbo_scraping()
	
	# start scraping the official notices from the fbo.gov website
	def start_fbo_scraping(self):
		return self.construct_fbo_list_query_request(FboDarpaSpider.fbo_start_url, self.parse_initial_fbo_solicitation_list)
	
	
	def parse_initial_fbo_solicitation_list(self, response):
		'''
		retrieve some meta information about the initial FBO query results, e.g.
		how many pages are there total, and generate queries for each list page 
		(i.e. 1, 2, 3, ..., last). Each list page will have at least one and at
		most <opportunities_per_page> notices.
		'''
		print "\n\n=========== Parsing Initial Notice Listing Page ==============\n"
		
		x_of_y_pages_pattern = re.compile(r"\d\s[-]\s\d\d?\d?\s(?:of)\s(\d+)")
		x_of_y_pages = str(response.xpath("//span[@class='lst-cnt']/text()")[0].extract())
		self.num_opportunities_found = num_ops = int(x_of_y_pages_pattern
													.match(x_of_y_pages).group(1))
		ops_per_page = FboDarpaSpider.opportunities_per_page;
		
		# Number of result list pages to traverse after the initial query
		self.list_page_number = num_pages = num_ops / ops_per_page + int(num_ops % ops_per_page > 0)
		
		# tweak the base url to generate urls for each page of result listing
		base_url = FboDarpaSpider.fbo_start_url
		list_page_urls = [base_url + "&pageID=" + str(page_id) for page_id in range(1, num_pages + 1)]
		
		# generate new request list
		requests = [self.construct_fbo_list_query_request(url, self.parse_fbo_solicitations_list_page) for url in list_page_urls]

		for request in requests:
			yield request
	
	def construct_fbo_notice_request(self, url, callback):
		'''
		build and return a single query for a single FBO notice
		@param url The get url to build around (containing the notice's unique identifier internal to fbo.gov)
		@type url String
		@param callback Callback function
		@type callback Function
		'''
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
	
	def parse_fbo_solicitations_list_page(self, response):
		'''
		parse the FBO opportunitues list page (go down the list and generate query for each notice link)
		'''
		print "\n\n=========== Parsing Notice Listing Page =============="
		print "=========== From URL: " + response.url + "\n"
		
		notice_urls = response.xpath("//a[@class='lst-lnk-notice']/@href").extract()
		# prepend with index, and ensure we're using "Complete View" to get all synopsis details if necessary
		notice_urls = [FboDarpaSpider.fbo_index_url + str(url).replace("&_cview=0", "&_cview=1") for url in notice_urls]
		solns = [str(soln.strip()) for soln in response.xpath("//div[@class='soln']/text()").extract()]
		
		#if these lengths don't match, something is wrong here
		if(len(notice_urls) != len(solns)):
			raise RuntimeError("Parsed fbo.gov solicitation url number ("
							+str(len(notice_urls))
							+") does not match number of parsed solicitation ids/numbers (" 
							+ str(len(solns)) + ").")
			
		#check against the dictionary of solicitations we already have.
		filtered_notice_urls = []
		for sol_ix in xrange(len(notice_urls)):
			if not self.db.contains(solns[sol_ix]):
				#skip if we alread have this one
				filtered_notice_urls.append(notice_urls[sol_ix])
			else:
				#report
				print "======= SKIPPING " + solns[sol_ix] + " (already in database) ====== "

		requests = [self.construct_fbo_notice_request(url, self.parse_fbo_solicitation) 
				for url in filtered_notice_urls]
		for request in requests:
			yield request

	def parse_fbo_solicitation(self, response):
		'''
		parse the FBO notice itself
		@param response The response object containing the page with the notice.
		@type Response scrapy.http.Response
		'''
		sponsor_number = str(response.xpath("//div[@id='dnf_class_values_procurement_notice__solicitation_number__widget']/text()")[0].extract()).strip()
		if(self.db.contains(sponsor_number)):
			# report
			print "======= SKIPPING (already in database) ======"
			#alread have this one, skip
			return
		
		bad_date = False
		check_office_wide = False
		filtered = False
		print "\n============== Parsing Single Notice ====================="
		print "============== From: " + response.url
		#=================== GET DEADLINE DATE=================================#
		date_xpath = "//div[@id='dnf_class_values_procurement_notice__response_deadline__widget']/text()"
		full_date_string = response.xpath(date_xpath)[0].extract()
		
		date_pattern = r"(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s\d\d?,\s\d\d\d\d"
		proper_date_string_matches = response.xpath(date_xpath)[0].re(date_pattern)
		if(full_date_string.strip() == u"-"):
			bad_date = True
			if(not self.dont_filter_continous):
				# report
				print "======= FILTERING AS CONTINOUS-SUBMISSION-DATE ======"
				# not a real date, assume continuous submission date, in which case filter this notice 
				filtered = True
		
		if(len(proper_date_string_matches) != 1):
			print "===> Bad deadline detected, \"" + repr(full_date_string) + "\". Attempting to use the Original Response Date field instead."
			deadline_date = None
			bad_date = True
		
		#try getting the original deadline instead
		if(bad_date):
			date_xpath = "//div[@id='dnf_class_values_procurement_notice__original_response_deadline__widget']/text()"
			if(len(response.xpath(date_xpath)) == 1):
				full_date_string = response.xpath(date_xpath)[0].extract()
				proper_date_string_matches = response.xpath(date_xpath)[0].re(date_pattern)
		
		if(len(proper_date_string_matches) > 0):
			first_match = str(proper_date_string_matches[0].strip())
			try:
				# try 3-letter month
				deadline_date = time.strptime(first_match, "%b %d, %Y")
			except(ValueError):
				# try full month name
				deadline_date = time.strptime(first_match, "%B %d, %Y")
		
		opp = Opportunity()
		if(deadline_date):
			# convert date to string in the [Month (2 char) / Day (2 char) / Year (4 char)] format
			date_string = time.strftime("%m/%d/%Y", deadline_date)
		else:
			try:
				date_string = str(full_date_string.strip())
			except:
				date_string = repr(full_date_string.strip())
		opp["deadline_date"] = date_string
		
		#=================== GET & PROCESS TITLE ==============================#
		opp_title = response.xpath("//div[@class='agency-header-w']/div/h2/text()")[0].extract()
		
		office_wide_pattern = re.compile(r"Office\s*\-?\s*Wide", re.IGNORECASE)
		
		# check for "Office-Wide" in the title
		if(len(re.findall(office_wide_pattern, opp_title)) > 0):
			check_office_wide = True
			if(not self.dont_filter_office_wide):
				# report
				print "======= FILTERING AS OFFICE-WIDE ======"
				filtered = True
				
				
		opp["opportunity_title"] = opp_title
		
		#================== THE EASY STUFF (sponsor num, announcement type, url)
		
		
		opp["sponsor_number"] = sponsor_number
		
		opp["announcement_type"] = str(response.xpath("//div[@id='dnf_class_values_procurement_notice__procurement_type__widget']/text()")[0].extract().strip())
		opp["program_url"] = response.url
		
		#============= GET & PROCESS SYNOPSIS (this is tough) =================#
		opp["synopsis"] = u""
		full_desc = response.xpath("//div[@id='dnf_class_values_procurement_notice__description__widget']")[0].extract()
		
		# some <p> tags have formatting, or perhaps...
		# some idiot hand-pasted an entry from another website / text document 
		# and did not remove the formatting, hence the complicated query
		desc_text_query = ("./body/div/text()|./body/div/p/text()|"  # regular text & paragraphs
						+ "./body/div/p/span/text()|./body/div/p/span/span/text()|"  # some queer line spacing & kerning 
						+ "/body/div/p/strong/text()|"  # some bold text / headers
						+ "./body/div/div/span[@class='added']/text()")  # the dates entries were added
		sel = Selector(text=full_desc).xpath(desc_text_query).extract()
		
		newline = u'\u000D\u000A'
		if(len(sel) > 100):  # crazy formatting! Collapse (don't insert newlines except for dates)
			entr_date_pattern = re.compile(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d\d?,\s\d\d\d\d\s\d\d?:\d\d?\d\s(?:pm|am)')
			sel = [entry.strip() + newline if entr_date_pattern.match(entry) or entry == u'Added:' else entry for entry in sel]
		else:
			# insert newlines for all entries
			# trim whitespace
			sel = [entry.strip() + newline for entry in sel]
			# get rid of newline for last entry
			sel[len(sel) - 1] = sel[len(sel) - 1].strip()
				
		desc_text = u''.join(sel)
		# convert html special characters to unicode
		try:
			desc_text = re.sub(r'&([^;]+);', lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), desc_text)
		except(KeyError):
			pass  # ignore step
		
		desc_text = desc_text.strip()  # remove trailing newlines
		
		# check for "Office-Wide" in the synopsis
		if(len(re.findall(office_wide_pattern, desc_text)) > 0):
			check_office_wide = True
		
		opp["synopsis"] = desc_text
		
		#============GET OFFICE & MARK HAND-CHECK FLAGS========================#
		
		if sponsor_number in self.darpa_announcement_dict:
			opp["office"] = self.darpa_announcement_dict[sponsor_number]
			opp["check_office"] = False
		else:
			opp["office"] = ""
			opp["check_office"] = True
		
		opp["check_date"] = bad_date
		opp["check_office_wide"] = check_office_wide
		opp["filtered"] = filtered
		yield opp
