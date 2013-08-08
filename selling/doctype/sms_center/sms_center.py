# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes

from webnotes.utils import cstr
from webnotes.model import db_exists
from webnotes.model.bean import copy_doclist
from webnotes.model.code import get_obj
from webnotes import msgprint
import requests
sql = webnotes.conn.sql
  
# ----------

class DocType:
  def __init__(self, doc, doclist=[]):
    self.doc = doc
    self.doclist = doclist
      
  ''' 
  * Changed by Indictrans
  * Converted field selection to link field 
  * Removed a condition from All Customer Contact, All Supplier Contact and All Sales Partner Contact to check if it has been created by customer/supplier/sales partner.
  * Removed a join query from All Employees and fetched from single table

  '''
  def create_receiver_list(self):
    rec, where_clause = '', ''   
    if self.doc.cus == 'All Customer Contact':
      where_clause = self.doc.customer and " and customer = '%s'" % self.doc.customer or " and ifnull(is_customer, 0) = 1"
    if self.doc.cus == 'All Supplier Contact':
      where_clause = self.doc.supplier and "  and supplier = '%s'" % self.doc.supplier or " and ifnull(is_supplier, 0) = 1"
    if self.doc.cus == 'All Sales Partner Contact':
      where_clause = self.doc.sales_partner and "  and sales_partner = '%s'" % self.doc.sales_partner or " and ifnull(is_sales_partner, 0) = 1"
    if self.doc.cus in ['All Customer Contact', 'All Supplier Contact', 'All Sales Partner Contact']:
      rec = sql("select CONCAT(ifnull(first_name,''),' ',ifnull(last_name,'')), mobile_no from `tabContact` where ifnull(mobile_no,'')!='' and docstatus != 2 %s" % where_clause)
    elif self.doc.cus == 'All Lead (Open)':
      rec = sql("select lead_name, mobile_no from tabLead where ifnull(mobile_no,'')!='' and docstatus != 2 and status = 'Open'")
    elif self.doc.cus == 'All Employee (Active)':
      where_clause = self.doc.department and " and department = '%s'" % self.doc.department or ""
      where_clause += self.doc.branch and " and branch = '%s'" % self.doc.branch or ""
      rec = sql("select employee_name, cell_number from `tabEmployee` where status = 'Active' and docstatus < 2 and ifnull(cell_number,'')!='' %s" % where_clause)
    elif self.doc.cus == 'All Sales Person':
      rec = sql("select sales_person_name, mobile_no from `tabSales Person` where docstatus != 2 and ifnull(mobile_no,'')!=''")
    elif self.doc.cus == 'All Contact':
      rec = sql("select first_name,mobile_no from `tabContact` where ifnull(mobile_no,'')!=''")
    else:
      rec=sql("select cont_name,ph_no from `tabSub Contact` where parent='"+self.doc.cus+"'")
    rec_list = ''
    for d in rec:
      rec_list += d[0] + ' - ' + d[1] + '\n'
    self.doc.receiver_list = rec_list
    webnotes.errprint(rec_list)
  def get_receiver_nos(self):
    receiver_nos = []
    for d in self.doc.receiver_list.split('\n'):
      receiver_no = d
      #if '-' in d:
      #  receiver_no = receiver_no.split('-')[1]
      #if receiver_no.strip():
      receiver_nos.append(cstr(receiver_no))
    return receiver_nos

  def get_down(self,ur):
        doctypelist = webnotes.get_doctype("Journal Voucher")
        naming_options = doctypelist.get_options("naming_series")
        voucher_type = doctypelist.get_options("voucher_type")

        #if template_type=="Two Accounts":
        #        extra_note = ""
        re = sql("select name from `tabCustomer`")
       
        columns='''"name"'''
        for (name) in re:
          #columns+="\n\""+cstr(name)+"\",\""+cstr(customer)+"\",\""+cstr(status1)+"\""
	  columns+="\n\""+cstr(name)+"\""
        webnotes.response['result'] = '''%(columns)s
'''% {
                
                "user_fmt": webnotes.defaults.get_global_default('date_format'),
                "default_company": webnotes.conn.get_default("company"),
                "naming_options": naming_options.replace("", " "),
                "voucher_type": voucher_type.replace("", ""),
                "columns": columns
        }
        webnotes.response['type'] = 'csv'
        webnotes.response['doctype'] = "Voucher-Import-%s" % template_type

  '''
  * Send SMS functionality
  '''

  def send_sms(self):
      receiver_list = self.get_receiver_nos()
      if self.doc.chhk==1:
        if receiver_list:
          for z in range(0,len(receiver_list)-1):
            a=cstr(receiver_list[z]).split('-')
            d1="Hi "+cstr(a[0])+" "+self.doc.message
          msgprint(get_obj('SMS Control', 'SMS Control').send_sms(receiver_list, cstr(d1)))
        else:
          msgprint("Receive List Is Empty")
      else:
        if receiver_list:
          msgprint(get_obj('SMS Control', 'SMS Control').send_sms(receiver_list, cstr(self.doc.message)))
        else:
          msgprint("Receive List Is Empty")

