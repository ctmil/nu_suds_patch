# -*- coding: utf-8 -*-

from openerp import tools, models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError
from StringIO import StringIO
import urllib2, httplib, urlparse, gzip, requests, json
import openerp.addons.decimal_precision as dp
import logging
import datetime
import time
from openerp.fields import Date as newdate
from datetime import datetime,date,timedelta

from suds.client import Client

class pos_order(models.Model):
	_inherit = 'pos.order'

	calculated_invoice_a = fields.Integer('calculated_invoice_a')
	calculated_invoice_b = fields.Integer('calculated_invoice_b')


	@api.multi
	def fp_print(self):
		#import pdb;pdb.set_trace()
		param = self.env['ir.config_parameter'].search([('key','=','sap_wsdl')])
		if not param:
			raise osv.except_osv('No existe parametro WSDL')
		try:
			client = Client("file:"+param.value)
		except:
			raise osv.except_osv('Problemas abriendo archivo WSDL')
		for order in self:
			#if '[ERR]' in order.nu_doc: 
			#	raise osv.except_osv('Error''No se puede imprimir un documento con error')
			if order.pos_reference and len(order.pos_reference) > 0:
				raise ValidationError('No se puede imprimir una orden ya  impresa')
				#raise osv.except_osv(cr,uid,'Error No se puede imprimir una orden ya impresa')
			if not order.partner_id.document_number:
				raise ValidationError('Error Falta DNI al cliente')
			if order.amount_total == 0:
				raise ValidationError('No se puede imprimir un ticket con monto 0')
			#if order.amount_total > 0:
			#	bill_resp = client.service.ZiowsBillPrint(order.nu_doc)
			#	if bill_resp.EBillDoc == "":
			#		raise ValidationError('Ticket cancelado')
	
			vals_numbers = {
				'calculated_invoice_a': order.next_invoice_a,
				'calculated_invoice_b': order.next_invoice_b,
				}
			order.write(vals_numbers)	
			data = {
				'pos_session_id': order.session_id.id,
				'id': order.id,
				'uid': order.user_id.id,
				'partner_id': order.partner_id.id,
				}
			vals = {'data': data}
			if not order.is_return:
				res = self.env['pos.order'].create_from_ui_v3([vals])
			else:
				res = self.env['pos.order'].create_refund_from_ui_v3([vals])
			# ZiowsSaveTktNum
			if order.nu_doc and order.pos_reference:
				return_value = client.service.ZiowsSaveTktNum(order.nu_doc,order.pos_reference[5:13])
				vals_order = {
					'sap_return': return_value
					}
				order.write(vals_order)
                        if order.pos_reference:
                                z_session_id = self.env['pos.session'].search([('state','=','opened')],limit=1)
                                if z_session_id:
                                        vals_order['z_session_id'] = z_session_id.id
                                order.write(vals_order)



