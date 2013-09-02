// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
// License: GNU General Public License v3. See license.txt

wn.require('app/utilities/doctype/sms_control/sms_control.js');
wn.require('app/setup/doctype/contact_control/contact_control.js');

wn.provide("erpnext");
erpnext.LeadController = wn.ui.form.Controller.extend({
	setup: function() {
		this.frm.fields_dict.customer.get_query = function(doc,cdt,cdn) {
				return { query:"controllers.queries.customer_query" } }
	},
	
	onload: function() {
		if(cur_frm.fields_dict.lead_owner.df.options.match(/^Profile/)) {
			cur_frm.fields_dict.lead_owner.get_query = function(doc,cdt,cdn) {
				return { query:"controllers.queries.profile_query" } }
		}

		if(cur_frm.fields_dict.contact_by.df.options.match(/^Profile/)) {
			cur_frm.fields_dict.contact_by.get_query = function(doc,cdt,cdn) {
				return { query:"controllers.queries.profile_query" } }
		}

		if(in_list(user_roles,'System Manager')) {
			cur_frm.footer.help_area.innerHTML = '<hr>\
				<p><a href="#Form/Sales Email Settings">Sales Email Settings</a><br>\
				<span class="help">Automatically extract Leads from a mail box e.g. "sales@example.com"</span></p>';
		}
	},
	
	refresh: function() {
		var doc = this.frm.doc;
		erpnext.hide_naming_series();
		this.frm.clear_custom_buttons();
		
		this.frm.dashboard.reset(doc);
		if(!doc.__islocal) {
			if(doc.status=="Converted") {// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
// License: GNU General Public License v3. See license.txt

cur_frm.fields_dict.customer.get_query = function(doc,cdt,cdn) {
	return{	query:"controllers.queries.customer_query" } }

wn.provide("erpnext.support");
// TODO commonify this code
erpnext.support.CustomerIssue = wn.ui.form.Controller.extend({
	customer: function() {
		var me = this;
		if(this.frm.doc.customer) {
			return this.frm.call({
				doc: this.frm.doc,
				method: "set_customer_defaults",
			});			
		}
	}
});

$.extend(cur_frm.cscript, new erpnext.support.CustomerIssue({frm: cur_frm}));

$.extend(cur_frm.cscript, {
	onload: function(doc, dt, dn) {
		if(in_list(user_roles,'System Manager')) {
			cur_frm.footer.help_area.innerHTML = '<p><a href="#Form/Email Settings/Email Settings">Email Settings</a><br>\
				<span class="help">Integrate incoming support emails to Support Ticket</span></p>';
		}
	},
	
	refresh: function(doc) {
		erpnext.hide_naming_series();
		cur_frm.cscript.make_listing(doc);
		if(!doc.__islocal) {
			if(cur_frm.fields_dict.status.get_status()=="Write") {
				if(doc.status!='Closed') cur_frm.add_custom_button('Close Ticket', cur_frm.cscript['Close Ticket']);
				if(doc.status=='Closed') cur_frm.add_custom_button('Re-Open Ticket', cur_frm.cscript['Re-Open Ticket']);
			}
			
			cur_frm.toggle_enable(["subject", "raised_by"], false);
			cur_frm.toggle_display("description", false);
		}
		refresh_field('status');
	},
	
	make_listing: function(doc) {
		var wrapper = cur_frm.fields_dict['thread_html'].wrapper;
		
		var comm_list = wn.model.get("Communication", {"parent": doc.name, "parenttype":"Lead"})
							
		cur_frm.communication_view = new wn.views.CommunicationList({
			list: comm_list,
			parent: wrapper,
			doc: doc,
			recipients: doc.raised_by
		})

	},
		
	'Close Ticket': function() {
		cur_frm.cscript.set_status("Closed");
	},
	
	'Re-Open Ticket': function() {
		cur_frm.cscript.set_status("Open");
	},

	set_status: function(status) {
		return wn.call({
			method:"support.doctype.support_ticket.support_ticket.set_status",
			args: {
				name: cur_frm.doc.name,
				status: status
			},
			callback: function(r) {
				if(!r.exc) cur_frm.reload_doc();
			}
		})
		
	}
	
})


				this.frm.dashboard.set_headline_alert(wn._("Converted"), "alert-success", "icon-ok-sign");
			} else {
				this.frm.dashboard.set_headline_alert(wn._(doc.status), "alert-info", "icon-exclamation-sign");
			}
		}
		
		this.frm.__is_customer = this.frm.__is_customer || this.frm.doc.__is_customer;
		if(!this.frm.doc.__islocal && !this.frm.__is_customer) {
			this.frm.add_custom_button("Create Customer", this.create_customer);
			this.frm.add_custom_button("Create Opportunity", this.create_opportunity);
			this.frm.add_custom_button("Send SMS", this.frm.cscript.send_sms);
		}
		
		cur_frm.communication_view = new wn.views.CommunicationList({
			list: wn.model.get("Communication", {"lead": this.frm.doc.name}),
			parent: this.frm.fields_dict.communication_html.wrapper,
			doc: this.frm.doc,
			recipients: this.frm.doc.email_id
		});
		
		if(!this.frm.doc.__islocal) {
			this.make_address_list();
		}
	},
	
	make_address_list: function() {
		var me = this;
		if(!this.frm.address_list) {
			this.frm.address_list = new wn.ui.Listing({
				parent: this.frm.fields_dict['address_html'].wrapper,
				page_length: 5,
				new_doctype: "Address",
				get_query: function() {
					return 'select name, address_type, address_line1, address_line2, \
					city, state, country, pincode, fax, email_id, phone, \
					is_primary_address, is_shipping_address from tabAddress \
					where lead="'+me.frm.doc.name+'" and docstatus != 2 \
					order by is_primary_address, is_shipping_address desc'
				},
				as_dict: 1,
				no_results_message: 'No addresses created',
				render_row: this.render_address_row,
			});
			// note: render_address_row is defined in contact_control.js
		}
		this.frm.address_list.run();
	}, 
	
	create_customer: function() {
		wn.model.open_mapped_doc({
			method: "selling.doctype.lead.lead.make_customer",
			source_name: cur_frm.doc.name
		})
	}, 
	
	create_opportunity: function() {
		wn.model.open_mapped_doc({
			method: "selling.doctype.lead.lead.make_opportunity",
			source_name: cur_frm.doc.name
		})
	}
});

$.extend(cur_frm.cscript, new erpnext.LeadController({frm: cur_frm}));