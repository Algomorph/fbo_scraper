'''
Created on Jun 23, 2015

@author: Gregory Kramida
@copyright: 2015 Gregory Kramida
'''
import pandas as pd
from pandas.io.excel import ExcelWriter
import os
from fbo_scraper.items import Opportunity
#from datetime import date
from datetime import datetime


class PandasExcelHelper(object):
    '''
    A helper class to help write notices to and read them from excel
    '''
    #how frequently to save the scraped items, i.e. interval of 5 means
    #5 items are saved at a time.
    save_interval = 1


    def __init__(self, db_filename = "fbo_solicitations.xlsx",
                 report_prefix = "report", 
                 sol_sheet_name = "solicitations",
                 filtered_sheet_name = "filtered_solicitations",
                 index_column = "sponsor_number",
                 report_only_new = True):
        '''
        Constructor
        '''
        if(not os.path.isfile(db_filename)):
            #generate a blank writable excel sheet from scratch
            field_names = [field_name for field_name in Opportunity.fields]
            field_names.remove("filtered")
            writer = ExcelWriter(db_filename)
            sol_df = pd.DataFrame(columns = field_names)
            filtered_df = pd.DataFrame(columns = field_names)
            sol_df.to_excel(writer,sol_sheet_name)
            filtered_df.to_excel(writer,filtered_sheet_name)
            writer.save()
            writer.close()
        
        self.report_filename = (report_prefix + "_" 
                                + str(datetime.today())[:19]
                                .replace(":","_").replace(" ","[") + "].xlsx")
        #kept for posterity, in case only the date component is needed and we don't care about overwrites
        #self.report_filename = report_prefix + "_" + str(date.today())
        self.db_filename = db_filename
        self.sol_sheet_name = sol_sheet_name
        self.filtered_sheet_name = filtered_sheet_name
        self.sol_df = pd.read_excel(db_filename,sol_sheet_name, index_col = index_column)
        self.filtered_df = pd.read_excel(db_filename,filtered_sheet_name, index_col = index_column)
        self.usaved_sol_counter = 0
        self.sol_counter = 0
        self.added_items = set()
        
    
    def generate_report(self):
        '''
        Generates a separate excel report, consisting of non-award-type notices
        that are not yet overdue
        '''
        print "\n\n========  Generating report...  ========"
        today = datetime.today()
        df = self.sol_df.copy()
        df["dd"] = [datetime.strptime(dt, "%m/%d/%Y") for dt in df["deadline_date"].values]
        report_df = self.sol_df[(df["dd"] >= today) | (df["check_date"] == 1) 
                                & (df["announcement_type"] != "Award")]
        report_df["new"] = pd.Series([(1 if ix in self.added_items else 0 ) 
                                      for ix in report_df.index ],
                                      index=report_df.index)
        writer = ExcelWriter(self.report_filename)
        report_df.to_excel(writer,self.sol_sheet_name,merge_cells=False)
        writer.save()
        writer.close()
        
        print "========  Report Generated as " + self.report_filename + " ========\n"
        
        
    def add_item(self,item):
        '''
        Adds the item to the proper dataframe based on the "filtered" attribute
        [filtered == True] ==> self.filtered_df
        [filtered == False] ==> self.sol_df
        '''
        item = dict(item)
        
        filtered = item["filtered"]
        key = item["sponsor_number"]
        item_body = {}
        
        for field_name in item:
            if not field_name == "sponsor_number" and not field_name == "filtered":
                item_body[field_name] = item[field_name]
                
        
        item_series = pd.Series(name=key,data=item_body)
        
        if(filtered):
            self.filtered_df.loc[key] = item_series
        else:
            self.added_items.add(key)
            self.sol_df.loc[key] = item_series
            
        if(self.sol_counter < PandasExcelHelper.save_interval):
            self.sol_counter += 1
        else:
            self.sol_counter = 0
            self.save_all()

        
    def save_all(self):
        '''
        Dumps all solicitations in both databases to an excel file,
        into two separate spreadsheets: one for filtered items, the other
        for the remaining (relevant) items
        '''
        print "\n\n========  Saving solicitations...  ========"
        writer = ExcelWriter(self.db_filename)
        self.sol_df.to_excel(writer,self.sol_sheet_name,merge_cells=False)
        self.filtered_df.to_excel(writer,self.filtered_sheet_name,merge_cells=False)
        writer.save()
        writer.close()
        print "========  Done saving.  ========\n"
        
    def contains(self,key):
        '''
        Checks whether the key is present in either filtered or the unfiltered dataframe
        '''
        return key in self.sol_df.index or key in self.filtered_df.index