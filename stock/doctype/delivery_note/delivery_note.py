# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes

from webnotes.utils import cstr, flt, cint, add_days
from webnotes.model.bean import getlist
from webnotes.model.code import get_obj
from webnotes import msgprint, _
import webnotes.defaults
from webnotes.model.mapper import get_mapped_doclist



sql = webnotes.conn.sql

from controllers.selling_controller import SellingController

class DocType(SellingController):
	def __init__(self, doc, doclist=[]):
		self.doc = doc
		self.doclist = doclist
		self.tname = 'Delivery Note Item'
		self.fname = 'delivery_note_details'
		self.status_updater = [{
			'source_dt': 'Delivery Note Item',
			'target_dt': 'Sales Order Item',
			'join_field': 'prevdoc_detail_docname',
			'target_field': 'delivered_qty',
			'target_parent_dt': 'Sales Order',
			'target_parent_field': 'per_delivered',
			'target_ref_field': 'qty',
			'source_field': 'qty',
			'percent_join_field': 'prevdoc_docname',
			'status_field': 'delivery_status',
			'keyword': 'Delivered'
		}]
		
	def onload(self):
		billed_qty = webnotes.conn.sql("""select sum(ifnull(qty, 0)) from `tabSales Invoice Item`
			where docstatus=1 and delivery_note=%s""", self.doc.name)
		if billed_qty:
			total_qty = sum((item.qty for item in self.doclist.get({"parentfield": "delivery_note_details"})))
			self.doc.fields["__billing_complete"] = billed_qty[0][0] == total_qty
		
	def get_contact_details(self):
		return get_obj('Sales Common').get_contact_details(self,0)


	def get_comm_rate(self, sales_partner):
		"""Get Commission rate of Sales Partner"""
		return get_obj('Sales Common').get_comm_rate(sales_partner, self)

	def set_actual_qty(self):
		for d in getlist(self.doclist, 'delivery_note_details'):
			if d.item_code and d.warehouse:
				actual_qty = sql("select actual_qty from `tabBin` where item_code = '%s' and warehouse = '%s'" % (d.item_code, d.warehouse))
				d.actual_qty = actual_qty and flt(actual_qty[0][0]) or 0


	def get_barcode_details(self, barcode):
		return get_obj('Sales Common').get_barcode_details(barcode)


	def get_adj_percent(self, arg=''):
		"""Re-calculates Basic Rate & amount based on Price List Selected"""
		get_obj('Sales Common').get_adj_percent(self)

	def get_rate(self,arg):
		return get_obj('Sales Common').get_rate(arg)

	def so_required(self):
		"""check in manage account if sales order required or not"""
		if webnotes.conn.get_value("Selling Settings", None, 'so_required') == 'Yes':
			 for d in getlist(self.doclist,'delivery_note_details'):
				 if not d.prevdoc_docname:
					 msgprint("Sales Order No. required against item %s"%d.item_code)
					 raise Exception


	def validate(self):
		super(DocType, self).validate()
		
		import utilities
		utilities.validate_status(self.doc.status, ["Draft", "Submitted", "Cancelled"])

		self.so_required()
		self.validate_proj_cust()
		sales_com_obj = get_obj(dt = 'Sales Common')
		sales_com_obj.check_stop_sales_order(self)
		sales_com_obj.check_active_sales_items(self)
		sales_com_obj.get_prevdoc_date(self)
		self.validate_for_items()
		self.validate_warehouse()
		self.validate_uom_is_integer("stock_uom", "qty")
		
		sales_com_obj.validate_max_discount(self, 'delivery_note_details')
		sales_com_obj.check_conversion_rate(self)

		# Set actual qty for each item in selected warehouse
		self.update_current_stock()
		
		self.validate_with_previous_doc()
		
		self.doc.status = 'Draft'
		if not self.doc.installation_status: self.doc.installation_status = 'Not Installed'	
		
	def validate_with_previous_doc(self):
		prev_doctype = [d.prevdoc_doctype for d in self.doclist.get({
			"parentfield": "delivery_note_details"}) if cstr(d.prevdoc_doctype) != ""]
			
		if prev_doctype:
			super(DocType, self).validate_with_previous_doc(self.tname, {
				prev_doctype[0]: {
					"ref_dn_field": "prevdoc_docname",
					"compare_fields": [["customer", "="], ["company", "="], ["project_name", "="],
						["currency", "="]],
				},
			})
			if cint(webnotes.defaults.get_global_default('maintain_same_sales_rate')):
				super(DocType, self).validate_with_previous_doc(self.tname, {
					prev_doctype[0] + " Item": {
						"ref_dn_field": "prevdoc_detail_docname",
						"compare_fields": [["export_rate", "="]],
						"is_child_table": True
					}
				})
			
		
	def validate_proj_cust(self):
		"""check for does customer belong to same project as entered.."""
		if self.doc.project_name and self.doc.customer:
			res = sql("select name from `tabProject` where name = '%s' and (customer = '%s' or ifnull(customer,'')='')"%(self.doc.project_name, self.doc.customer))
			if not res:
				msgprint("Customer - %s does not belong to project - %s. \n\nIf you want to use project for multiple customers then please make customer details blank in project - %s."%(self.doc.customer,self.doc.project_name,self.doc.project_name))
				raise Exception

	def validate_for_items(self):
		check_list, chk_dupl_itm = [], []
		for d in getlist(self.doclist,'delivery_note_details'):
			e = [d.item_code, d.description, d.warehouse, d.prevdoc_docname or '', d.batch_no or '']
			f = [d.item_code, d.description, d.prevdoc_docname or '']

			if webnotes.conn.get_value("Item", d.item_code, "is_stock_item") == 'Yes':
				if e in check_list:
					msgprint("Please check whether item %s has been entered twice wrongly." 
						% d.item_code)
				else:
					check_list.append(e)
			else:
				if f in chk_dupl_itm:
					msgprint("Please check whether item %s has been entered twice wrongly." 
						% d.item_code)
				else:
					chk_dupl_itm.append(f)

	def validate_warehouse(self):
		for d in self.get_item_list():
			if webnotes.conn.get_value("Item", d['item_code'], "is_stock_item") == "Yes":
				if not d['warehouse']:
					msgprint("Please enter Warehouse for item %s as it is stock item"
						% d['item_code'], raise_exception=1)


	def update_current_stock(self):
		for d in getlist(self.doclist, 'delivery_note_details'):
			bin = sql("select actual_qty from `tabBin` where item_code = %s and warehouse = %s", (d.item_code, d.warehouse), as_dict = 1)
			d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0

		for d in getlist(self.doclist, 'packing_details'):
			bin = sql("select actual_qty, projected_qty from `tabBin` where item_code =	%s and warehouse = %s", (d.item_code, d.warehouse), as_dict = 1)
			d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0
			d.projected_qty = bin and flt(bin[0]['projected_qty']) or 0
			
	def on_update(self):
		self.doclist = get_obj('Sales Common').make_packing_list(self,'delivery_note_details')

	def on_submit(self):
		self.validate_packed_qty()

		# Check for Approving Authority
		get_obj('Authorization Control').validate_approving_authority(self.doc.doctype, self.doc.company, self.doc.grand_total, self)
		
		# update delivered qty in sales order	
		self.update_prevdoc_status()
		
		# create stock ledger entry
		self.update_stock_ledger(update_stock = 1)
		self.update_serial_nos()

		self.credit_limit()
		
		self.set_buying_amount()
		self.make_gl_entries()

		# set DN status
		webnotes.conn.set(self.doc, 'status', 'Submitted')


	def on_cancel(self):
		sales_com_obj = get_obj(dt = 'Sales Common')
		sales_com_obj.check_stop_sales_order(self)
		self.check_next_docstatus()
				
		self.update_prevdoc_status()
		
		self.update_stock_ledger(update_stock = -1)
		self.update_serial_nos(cancel=True)

		webnotes.conn.set(self.doc, 'status', 'Cancelled')
		self.cancel_packing_slips()
		
		self.make_cancel_gl_entries()

	def update_serial_nos(self, cancel=False):
		from stock.doctype.stock_ledger_entry.stock_ledger_entry import update_serial_nos_after_submit, get_serial_nos
		update_serial_nos_after_submit(self, "Delivery Note", "delivery_note_details")
		update_serial_nos_after_submit(self, "Delivery Note", "packing_details")

		for table_fieldname in ("delivery_note_details", "packing_details"):
			for d in self.doclist.get({"parentfield": table_fieldname}):
				for serial_no in get_serial_nos(d.serial_no):
					sr = webnotes.bean("Serial No", serial_no)
					if cancel:
						sr.doc.status = "Available"
						for fieldname in ("warranty_expiry_date", "delivery_document_type", 
							"delivery_document_no", "delivery_date", "delivery_time", "customer", 
							"customer_name"):
							sr.doc.fields[fieldname] = None
					else:
						sr.doc.delivery_document_type = "Delivery Note"
						sr.doc.delivery_document_no = self.doc.name
						sr.doc.delivery_date = self.doc.posting_date
						sr.doc.delivery_time = self.doc.posting_time
						sr.doc.customer = self.doc.customer
						sr.doc.customer_name	= self.doc.customer_name
						if sr.doc.warranty_period:
							sr.doc.warranty_expiry_date	= add_days(cstr(self.doc.posting_date), 
								cint(sr.doc.warranty_period))
						sr.doc.status =	'Delivered'

					sr.save()

	def validate_packed_qty(self):
		"""
			Validate that if packed qty exists, it should be equal to qty
		"""
		if not any([flt(d.fields.get('packed_qty')) for d in self.doclist if
				d.doctype=='Delivery Note Item']):
			return
		packing_error_list = []
		for d in self.doclist:
			if d.doctype != 'Delivery Note Item': continue
			if flt(d.fields.get('qty')) != flt(d.fields.get('packed_qty')):
				packing_error_list.append([
					d.fields.get('item_code', ''),
					d.fields.get('qty', 0),
					d.fields.get('packed_qty', 0)
				])
		if packing_error_list:
			err_msg = "\n".join([("Item: " + d[0] + ", Qty: " + cstr(d[1]) \
				+ ", Packed: " + cstr(d[2])) for d in packing_error_list])
			webnotes.msgprint("Packing Error:\n" + err_msg, raise_exception=1)

	def check_next_docstatus(self):
		submit_rv = sql("select t1.name from `tabSales Invoice` t1,`tabSales Invoice Item` t2 where t1.name = t2.parent and t2.delivery_note = '%s' and t1.docstatus = 1" % (self.doc.name))
		if submit_rv:
			msgprint("Sales Invoice : " + cstr(submit_rv[0][0]) + " has already been submitted !")
			raise Exception , "Validation Error."

		submit_in = sql("select t1.name from `tabInstallation Note` t1, `tabInstallation Note Item` t2 where t1.name = t2.parent and t2.prevdoc_docname = '%s' and t1.docstatus = 1" % (self.doc.name))
		if submit_in:
			msgprint("Installation Note : "+cstr(submit_in[0][0]) +" has already been submitted !")
			raise Exception , "Validation Error."

	def cancel_packing_slips(self):
		"""
			Cancel submitted packing slips related to this delivery note
		"""
		res = webnotes.conn.sql("""SELECT name FROM `tabPacking Slip` WHERE delivery_note = %s 
			AND docstatus = 1""", self.doc.name)

		if res:
			from webnotes.model.bean import Bean
			for r in res:
				ps = Bean(dt='Packing Slip', dn=r[0])
				ps.cancel()
			webnotes.msgprint(_("Packing Slip(s) Cancelled"))


	def update_stock_ledger(self, update_stock):
		self.values = []
		for d in self.get_item_list():
			if webnotes.conn.get_value("Item", d['item_code'], "is_stock_item") == "Yes":
				# this happens when item is changed from non-stock to stock item
				if not d["warehouse"]:
					continue
				
				if d['reserved_qty'] < 0 :
					# Reduce reserved qty from reserved warehouse mentioned in so
					if not d["reserved_warehouse"]:
						webnotes.throw(_("Reserved Warehouse is missing in Sales Order"))
						
					args = {
						"item_code": d['item_code'],
						"voucher_type": self.doc.doctype,
						"voucher_no": self.doc.name,
						"reserved_qty": flt(update_stock) * flt(d['reserved_qty']),
						"posting_date": self.doc.posting_date,
						"is_amended": self.doc.amended_from and 'Yes' or 'No'
					}
					get_obj("Warehouse", d["reserved_warehouse"]).update_bin(args)
						
				# Reduce actual qty from warehouse
				self.make_sl_entry(d, d['warehouse'], - flt(d['qty']) , 0, update_stock)
		
		get_obj('Stock Ledger', 'Stock Ledger').update_stock(self.values)


	def get_item_list(self):
	 return get_obj('Sales Common').get_item_list(self)


	def make_sl_entry(self, d, wh, qty, in_value, update_stock):
		self.values.append({
			'item_code'					: d['item_code'],
			'warehouse'					: wh,
			'posting_date'				: self.doc.posting_date,
			'posting_time'				: self.doc.posting_time,
			'voucher_type'				: 'Delivery Note',
			'voucher_no'				: self.doc.name,
			'voucher_detail_no'	 		: d['name'],
			'actual_qty'				: qty,
			'stock_uom'					: d['uom'],
			'incoming_rate'			 	: in_value,
			'company'					: self.doc.company,
			'fiscal_year'				: self.doc.fiscal_year,
			'is_cancelled'				: (update_stock==1) and 'No' or 'Yes',
			'batch_no'					: d['batch_no'],
			'serial_no'					: d['serial_no'],
			"project"					: self.doc.project_name
		})


	def credit_limit(self):
		"""check credit limit of items in DN Detail which are not fetched from sales order"""
		amount, total = 0, 0
		for d in getlist(self.doclist, 'delivery_note_details'):
			if not d.prevdoc_docname:
				amount += d.amount
		if amount != 0:
			total = (amount/self.doc.net_total)*self.doc.grand_total
			get_obj('Sales Common').check_credit(self, total)
		
	def make_gl_entries(self):
		if not cint(webnotes.defaults.get_global_default("auto_inventory_accounting")):
			return
			
		gl_entries = []	
		for item in self.doclist.get({"parentfield": "delivery_note_details"}):
			self.check_expense_account(item)
			
			if item.buying_amount:
				gl_entries += self.get_gl_entries_for_stock(item.expense_account, -1*item.buying_amount, 
					cost_center=item.cost_center)
				
		if gl_entries:
			from accounts.general_ledger import make_gl_entries
			make_gl_entries(gl_entries, cancel=(self.doc.docstatus == 2))

def get_invoiced_qty_map(delivery_note):
	"""returns a map: {dn_detail: invoiced_qty}"""
	invoiced_qty_map = {}
	
	for dn_detail, qty in webnotes.conn.sql("""select dn_detail, qty from `tabSales Invoice Item`
		where delivery_note=%s and docstatus=1""", delivery_note):
			if not invoiced_qty_map.get(dn_detail):
				invoiced_qty_map[dn_detail] = 0
			invoiced_qty_map[dn_detail] += qty
	
	return invoiced_qty_map

@webnotes.whitelist()
def make_sales_invoice(source_name, target_doclist=None):
	invoiced_qty_map = get_invoiced_qty_map(source_name)
	
	def update_accounts(source, target):
		si = webnotes.bean(target)
		si.doc.is_pos = 0
		si.run_method("onload_post_render")
		
		si.set_doclist(si.doclist.get({"parentfield": ["!=", "entries"]}) +
			si.doclist.get({"parentfield": "entries", "qty": [">", 0]}))
		
		if len(si.doclist.get({"parentfield": "entries"})) == 0:
			webnotes.msgprint(_("Hey! All these items have already been invoiced."),
				raise_exception=True)
				
		return si.doclist
		
	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = source_doc.qty - invoiced_qty_map.get(source_doc.name, 0)
	
	doclist = get_mapped_doclist("Delivery Note", source_name, 	{
		"Delivery Note": {
			"doctype": "Sales Invoice", 
			"validation": {
				"docstatus": ["=", 1]
			}
		}, 
		"Delivery Note Item": {
			"doctype": "Sales Invoice Item", 
			"field_map": {
				"name": "dn_detail", 
				"parent": "delivery_note", 
				"prevdoc_detail_docname": "so_detail", 
				"prevdoc_docname": "sales_order", 
				"serial_no": "serial_no"
			},
			"postprocess": update_item
		}, 
		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges", 
			"add_if_empty": True
		}, 
		"Sales Team": {
			"doctype": "Sales Team", 
			"field_map": {
				"incentives": "incentives"
			},
			"add_if_empty": True
		}
	}, target_doclist, update_accounts)
	
	return [d.fields for d in doclist]
	
@webnotes.whitelist()
def make_installation_note(source_name, target_doclist=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.installed_qty)
		target.prevdoc_date = source_parent.posting_date
		target.serial_no = obj.serial_no
	
	doclist = get_mapped_doclist("Delivery Note", source_name, 	{
		"Delivery Note": {
			"doctype": "Installation Note", 
			"validation": {
				"docstatus": ["=", 1]
			}
		}, 
		"Delivery Note Item": {
			"doctype": "Installation Note Item", 
			"field_map": {
				"name": "prevdoc_detail_docname", 
				"parent": "prevdoc_docname", 
				"parenttype": "prevdoc_doctype", 
			},
			"postprocess": update_item,
			"condition": lambda doc: doc.installed_qty < doc.qty
		}
	}, target_doclist)

	return [d.fields for d in doclist]