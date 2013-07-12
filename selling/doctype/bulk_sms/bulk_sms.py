# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
from webnotes import msgprint
from selling.doctype.sms_center.sms_center import Doctype

class DocType1(Doctype):
	def __init__(self, doc, doclist=[]):
		self.doc=doc 
		self.doclist = doclist

        def get_down(self,ur):
		msgprint(ur)
		

