import scrapy
import scrapy.http
import urllib

class FboDarpaSpider(scrapy.Spider):
	name = "fbo_darpa"
	allowed_domains = ["www.fbo.gov"]
	data_per_page = 100
	start_urls = [
        "https://www.fbo.gov/index?s=opportunity&mode=list&tab=list&tabmode=list&pp=100" + str(data_per_page)
    ]
	
	def make_requests_from_url(self, url):
		payload = {
			"dnf_class_values[procurement_notice][keywords]":"",
			"dnf_class_values[procurement_notice][_posted_date]":"",
			"dnf_class_values[procurement_notice][agency]":"048f413b4c64abc6c0afbc36b09f099d",
			"dnf_class_values[procurement_notice][zipstate]":"",
			"dnf_class_values[procurement_notice][procurement_type][]":"",
			"dnf_class_values[procurement_notice][set_aside][]":"",
			"dnf_class_values[procurement_notice][dnf_class_name]":"procurement_notice",
			"dnf_class_values[procurement_notice][notice_id]":"af741dd47e56d8a1b06c0a2788481f07",
			"dnf_class_values[procurement_notice][posted]":"",
			"autocomplete_input_dnf_class_values[procurement_notice][agency]":"Other Defense Agencies/Defense Advanced Research Projects Agency",
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
		yield [scrapy.http.Request(url, callback=self.parse_opportunities_list, 
								method="POST", body=urllib.urlencode(payload),
								headers=headers)]
		
	def parse_opportunities_list(self, response):
		page_select = response.xpath("//select[@name='setPerPage']")[0]
		pass