#~ # -*- coding: utf-8 -*-
from stoqdrivers.printers.fiscal import FiscalPrinter
from stoqdrivers.exceptions import (CommandParametersError,)
from stoqdrivers.enum import PaymentMethodType,TaxType,UnitType
from decimal import Decimal
import re
import os
import ConfigParser
from fiscalv import FiscalV
from invoice import fvInvoice
from stoqdrivers.exceptions import (PendingReduceZ,
                                    CouponOpenError,
                                    CloseCouponError,)

from osv import osv, fields
from openerp.osv import fields, osv, orm

class BematechV(osv.osv):
    _inherit = "account.invoice"

    _columns = {
        'workflow_process_id': fields.many2one('sale.workflow.process',
                                               string='Sale Workflow Process'),
        #TODO propose a merge to add this field by default in acount module
        'sale_ids': fields.many2many('sale.order', 'sale_order_invoice_rel',
                                     'invoice_id', 'order_id',
                                     string='Sale Orders')
    }

    def get_empresa(self, partner_id):
        obj_addr = self.pool.get('res.partner.address')
        addr_id =obj_addr.search(self.cr, self.uid, [('type','=','invoice'),('partner_id','=',partner_id)])
        res = {}
        for row in obj_addr.browse(self.cr, self.uid, addr_id):
            res = {
            'street':row.street,
            'phone':row.phone,
            'fax':row.fax,
            'email':row.email,
            'city':row.city,
            'name':row.name,
            'country':row.country_id.name,
            } 
        return res

BematechV()
class account_invoice_lines():
    
    _name='account_invoice_lines'
    _inherit = "account.invoice"

    def get_all(self, cr, uid, ids, part_obj,pagos,el_browser, context=None):
        printer = FiscalV(brand='bematech', model='MP2100', device='/dev/ttyS1')
        printer.cancel()
        invoiceBM = fvInvoice()
        el_socio_nombre = part_obj.display_name
        el_socio_rif = part_obj.name
        el_socio_direccion =self.get_Direccion_partner(cr, uid, part_obj, context=None)
                                                      
        invoiceBM.identify_customer(  customer_name    = el_socio_nombre,
                            customer_address = el_socio_direccion, 
                            customer_id      = el_socio_rif)    

        res = {}
        for invoice in el_browser:
            res[invoice.id] = {
                'producto':'',
                'description':'',
                'price':0.0,
                'tax':'',
                'quantity':0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            for line in invoice.invoice_line:
                la_linea = line.invoice_line_tax_id
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                res[invoice.id]['producto'] = '' #line.product_id.default_code
                res[invoice.id]['description'] = line.name
                la_tasa ='N1'
                if la_linea :
                   la_tasa ='01'
              #      la_tasa ='N1'
                res[invoice.id]['tax'] = line.product_id.taxes_id #line.tax_id [('01' , 'N1', [x.id for x in line.product_id.taxes_id] )]
                res[invoice.id]['price'] = line.price_unit
                res[invoice.id]['quantity'] = line.quantity
                invoiceBM.add_item(item_code    =  line.product_id.name_template[:13], 
                             item_description = line.name[:29],
                             item_price       = Decimal(line.price_unit),
                             taxcode          = la_tasa,
                             items_quantity   = Decimal(line.quantity), 
                             unit             = UnitType.EMPTY,
                             discount         = Decimal("0.0")) 
        
        for n in pagos:
            forma_tipo = '01'
            el_tipo=n['journal_id'].name_get()[0].__getitem__(0)
            if el_tipo==17:
               forma_tipo='01'
            elif el_tipo==6:
               forma_tipo ='04'
            elif el_tipo==5:  
               forma_tipo ='03'   
            invoiceBM.add_payment(payment_method = forma_tipo, #forma_tipo,
            payment_value  =  n['credit'])
        try:
           printer.print_invoice(invoiceBM.get_dict())
        except CouponOpenError:
           print "Printer has a coupon currently open, lets cancel"
           printer.cancel()
        except PendingReduceZ:
           print "Reporte Z"
           printer.close_till()
        except CloseCouponError as e:
          print "Could not close the coupon..."
        return res
    
    def get_Direccion_partner(self,cr, uid, partner_record, context=None):
        if not partner_record:
            return False
        st = partner_record.street or ''
        st1 = partner_record.street2 or ''
        zip = partner_record.zip or ''
        city = partner_record.city or  ''
        zip_city = zip + ' ' + city
        cntry = partner_record.country_id and partner_record.country_id.name or ''
        return st + " " + st1 + "\n" + zip_city + "\n" +cntry
    
    def get_tipo(self,cr, uid, tipo_record, context=None):
        if not tipo_record:
            return False
        retorno = tipo_record.journal_id 
        return retorno    

account_invoice_lines()
