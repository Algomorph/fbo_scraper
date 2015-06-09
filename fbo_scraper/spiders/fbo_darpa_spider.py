################################################################################
#    Author: Greg Kramida (github id: Algomorph)
# Copyright: (2015) Gregory Kramida
#   License: Apache V2
#            [That means (basically): feel free to modify, sell, 
#             whatever, just do not remove the original author's credits/notice 
#             from this file.] 
################################################################################

import scrapy
import scrapy.http
import urllib
import re

class FboDarpaSpider(scrapy.Spider):
	name = "fbo_darpa"
	#this number is specific for DARPA.
	#  see value attribute of <input id="dnf_class_values_procurement_notice__agency_" ...>
	#  after you type & choose the name of the desired agency on the fbo.gov front page.
	agency_id = "048f413b4c64abc6c0afbc36b09f099d"
	#this name is specific for DARPA. It may be nonessential, I (Algomorph) have not checked.
	#  see value attribute of <input id="autocomplete_input_dnf_class_values_procurement_notice__agency_" ...>
	#  after you type & choose the name of the desired agency on the fbo.gov front page. 
	agency_autocomplete_name = "Other Defense Agencies/Defense Advanced Research Projects Agency"
	allowed_domains = ["www.fbo.gov"]
	index_url = "https://www.fbo.gov/index"
	#number of opportunities per page
	opportunities_per_page = 100
	
	#Constructor
	def __init__(self,*args, **kwargs):
		self.data_params_determined = False 
		super(FboDarpaSpider, self).__init__(*args, **kwargs)
	
	
	start_urls = [
        FboDarpaSpider.index_url + "?s=opportunity&mode=list&tab=list&tabmode=list&pp=" 
        + str(opportunities_per_page)
    ]
	
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
			"dnf_opt_finalize":0,
			"dnf_opt_mode":"update",
			"dnf_opt_target":"",
			"dnf_opt_validate":1,
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
		return scrapy.http.Request(url, callback=callback, 
								method="POST", body=urllib.urlencode(payload),
								headers=headers)
		
	#@override
	#called to construct requests from start url(s)
	def make_requests_from_url(self, url):
		yield [self.construct_list_query_request(url, self.parse_opportunities_list)]
		
	def parse_initial_opportunities_list(self, response):
		pattern = re.compile("\d\s[-]\s\d\d?\d?\s(?:of)\s(\d+)")
		x_of_y_pages = str(response.xpath("//span[@class='lst-cnt']/text()")[0].extract())
		self.num_opportunities_found = num_ops = int(pattern.match(x_of_y_pages).group(1))
		ops_per_page = FboDarpaSpider.opportunities_per_page;
		#Number of result list pages to traverse after the initial query
		self.list_page_number = num_pages = num_ops / ops_per_page + int(num_ops % ops_per_page > 0)
		#tweak the base url to generate urls for each page of result listing
		base_url = FboDarpaSpider.start_urls[0]
		list_page_urls = [base_url + "&pageID=" + str(page_id) for page_id in range(1,num_pages+1)]
		#generate new request list
		requests = [self.construct_list_query_request(url,self.parse_opportunities_list_page) for url in list_page_urls]
		yield requests
		
	def parse_opportunities_list_page(self, response):
		
		pass