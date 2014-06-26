# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013 Camptocamp (<http://www.camptocamp.com>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
import re
import time
import openerp.netsvc as netsvc
from openerp import pooler
from openerp.addons.base_calendar import base_calendar
from openerp.osv import osv, fields
import cups
               
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties,ListLevelProperties, FontFace
from odf.text import P, H, A, S, List, ListItem, ListStyle, ListLevelStyleBullet,ListLevelStyleNumber, ListLevelStyleBullet, Span
from odf.text import Note, NoteBody, NoteCitation
from odf.office import FontFaceDecls
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.draw import Frame, Image


import os
import StringIO
import odt2txt


class virtual_report_spool(base_calendar.virtual_report_spool):

    def exp_report(self, db, uid, object, ids, datas=None, context=None):
        res = super(virtual_report_spool, self).exp_report(db, uid, object, ids, datas, context)
        self._reports[res]['report_name'] = object
        return res

    def exp_report_get(self, db, uid, report_id):

        cr = pooler.get_db(db).cursor()
        try:
            pool = pooler.get_pool(cr.dbname)
            # First of all load report defaults: name, action and printer
            report_obj = pool.get('ir.actions.report.xml')
            report = report_obj.search(cr,uid,[('report_name','=',self._reports[report_id]['report_name'])])
            if report:
                report = report_obj.browse(cr,uid,report[0])
                name = report.name
                data = report.behaviour()[report.id]
                action = data['action']
                printer = data['printer']
                if action != 'client':
                    if (self._reports and self._reports.get(report_id, False) and self._reports[report_id].get('result', False)
                        and self._reports[report_id].get('format', False)):
                        # especial redireccionamiento de documentos CTI-Denis
                        record = pool.get('account.invoice').browse(cr, uid,1, context=None)
                        copia = self._crea_reporte(db, cr, uid, record, report, printer, report_obj,report_id, context=None)
                        #CTI-Denis
                        
                        report_obj.print_direct(cr, uid, report.id, base64.encodestring(self._reports[report_id]['result']),
                            self._reports[report_id]['format'], printer)
                        
                        #report_obj.print_Copias(cr, uid, report.id, base64.encodestring(copia),
                        #    self._reports[report_id]['format'], printer)

                        
                        # XXX "Warning" removed as it breaks the workflow
                        # it would be interesting to have a dialog box to confirm if we really want to print
                        # in this case it must be with a by pass parameter to allow massive impression
                        #raise osv.except_osv(_('Printing...'), _('Document sent to printer %s') % (printer,))

        except:
            cr.rollback()
            raise
        finally:
            cr.close()

        res = super(virtual_report_spool, self).exp_report_get(db, uid, report_id)
        return res
    def _crea_reporte(self, db, cr, uid, record, report, printer,report_obj,report_id, context=None):
        """Utility method to generate the first PDF-type report declared for the
           current model with ``usage`` attribute set to ``default``.
           This must be called explicitly by models that need it, usually
           at the beginning of ``edi_export``, before the call to ``super()``."""
       
        textdoc = OpenDocumentText()
        p = P(text="ORDEN DE DESPACHO ")
        textdoc.text.addElement(p)
        
        p = P(text="Hola borisito ORDEN DE DESPACHO ")
        textdoc.text.addElement(p)

        textdoc.save("/home/master/PDF/Texto", True)
        
        el_texto = odt2txt.OpenDocumentTextFile("/home/master/PDF/Texto.odt").toString()
        self.creartxt(el_texto, "/home/master/PDF/Texto.txt")   
        
        report_obj.print_direct(cr, uid, report.id, base64.encodestring(el_texto),
                                self._reports[report_id]['format'], printer) 
        #self.creaodf()
            
        cr = pooler.get_db(db).cursor()
        pool = pooler.get_pool(cr.dbname)   
        ir_actions_report = pool.get('ir.actions.report.xml')
        matching_reports = ir_actions_report.search(cr, uid, [('model','=','account.invoice.Despacho'),
                                                              ('report_type','=','pdf'),
                                                              ('usage','=','default')])
        if matching_reports:
            report = ir_actions_report.browse(cr, uid, matching_reports[0])
            report_service = 'report.' + report.report_name
             
            # service = netsvc.LocalService(report_service)
            service = netsvc.LocalService('report.account.invoice')
            service.name ='report.account.despacho'
            service.tmpl='addons/account/report/account_print_despacho.rml' 
            #service.name=''
            (result, format) = service.create(cr, uid, [record.id], {'model': 'account.invoice'}, context=context)
            eval_context = {'time': time, 'object': record}
            if result:
                # no auto-saving of report as attachment, need to do it manually
                #result = base64.b64encode(result)
                #file_name = record.name_get()[0][1]
                #file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', file_name)
                #file_name += ".pdf"
                #pool.get('ir.attachment').create(cr, uid,
                #                                      {
                #                                       'name': file_name,
                #                                       'datas': result,
                #                                       'datas_fname': file_name,
                #                                       'res_model': 'Invoice.printer.copias',
                #                                       'res_id': record.id,
                #                                       'type': 'binary'
                #                                      },
                #                                      context=context)
                return result
    def creartxt(self,el_texto,el_nombre):
        archi=open(el_nombre,'w')
        archi.close()
        archi=open(el_nombre,'a')
        archi.write(el_texto)
        archi.close()
    def creaodf(self):
        # fname is the path for the output file
        fname= "/home/master/PDF/Despacho";
        textdoc = OpenDocumentText()
        # styles
        """
        <style:style style:name="Standard" style:family="paragraph" style:class="text"/>
        <style:style style:name="Text_20_body" style:display-name="Text body"
        style:family="paragraph"
        style:parent-style-name="Standard" style:class="text">
        <style:paragraph-properties fo:margin-top="0in" fo:margin-bottom="0.0835in"/>
        </style:style>
        """
        s = textdoc.styles
               
        StandardStyle = Style(name="Standard", family="paragraph")
        #StandardStyle.addAttribute('class','text')
        s.addElement(StandardStyle)
               
        TextBodyStyle = Style(name="Text_20_body",family="paragraph", 
        parentstylename='Standard', displayname="Text body")
        #TextBodyStyle.addAttribute('class','text')
        TextBodyStyle.addElement(ParagraphProperties(margintop="0in", 
        marginbottom="0.0835in"))
        s.addElement(TextBodyStyle)
        # font declarations
        """
        <office:font-face-decls>
        <style:font-face style:name="Arial" svg:font-family="Arial"
        style:font-family-generic="swiss"
        style:font-pitch="variable"/>
        </office:font-face-decls>
        """
        textdoc.fontfacedecls.addElement((FontFace(name="Arial",fontfamily="Arial", 
        fontfamilygeneric="swiss",fontpitch="variable")))
        # Automatic Style
        # P1
        """
        <style:style style:name="P1" style:family="paragraph"
        style:parent-style-name="Standard"
        style:list-style-name="L1"/>
        """
        P1style = Style(name="P1", family="paragraph", parentstylename="Standard", 
        liststylename="L1")
        textdoc.automaticstyles.addElement(P1style)
               
        # L1
        """
        <text:list-style style:name="L1">
        <text:list-level-style-bullet text:level="1"
        text:style-name="Numbering_20_Symbols"
        style:num-suffix="." text:bullet-char="•">
        <style:list-level-properties text:space-before="0.25in"
        text:min-label-width="0.25in"/>
        <style:text-properties style:font-name="StarSymbol"/>
        </text:list-level-style-bullet>
        </text:list-style>
        """
        L1style=ListStyle(name="L1")
        # u'\u2022' is the bullet character (http://www.unicode.org/charts/PDF/U2000.pdf)
        bullet1 = ListLevelStyleBullet(level="1", stylename="Numbering_20_Symbols", 
        numsuffix=".", bulletchar=u'\u2022')
        L1prop1 = ListLevelProperties(spacebefore="0.25in", minlabelwidth="0.25in")
        bullet1.addElement(L1prop1)
        L1style.addElement(bullet1)
        textdoc.automaticstyles.addElement(L1style)
               
        # P6
        """
        <style:style style:name="P6" style:family="paragraph"
        style:parent-style-name="Standard"
        style:list-style-name="L5"/>
        """
               
        P6style = Style(name="P6", family="paragraph", parentstylename="Standard", 
        liststylename="L5")
        textdoc.automaticstyles.addElement(P6style)
               
        # L5
        """
        <text:list-style style:name="L5">
        <text:list-level-style-number text:level="1"
        text:style-name="Numbering_20_Symbols"
        style:num-suffix="." style:num-format="1">
        <style:list-level-properties text:space-before="0.25in"
        text:min-label-width="0.25in"/>
        </text:list-level-style-number>
        </text:list-style>
        """
               
        L5style=ListStyle(name="L5")
        numstyle1 = ListLevelStyleNumber(level="1", stylename="Numbering_20_Symbols", 
        numsuffix=".", numformat='1')
        L5prop1 = ListLevelProperties(spacebefore="0.25in", minlabelwidth="0.25in")
        numstyle1.addElement(L5prop1)
        L5style.addElement(numstyle1)
        textdoc.automaticstyles.addElement(L5style)
               
        # T1
        """
        <style:style style:name="T1" style:family="text">
        <style:text-properties fo:font-style="italic" style:font-style-asian="italic"
        style:font-style-complex="italic"/>
        </style:style>
        """
        T1style = Style(name="T1", family="text")
        T1style.addElement(TextProperties(fontstyle="italic",fontstyleasian="italic",
        fontstylecomplex="italic"))
        textdoc.automaticstyles.addElement(T1style)
               
        # T2
        """
        <style:style style:name="T2" style:family="text">
        <style:text-properties fo:font-weight="bold" style:font-weight-asian="bold"
        style:font-weight-complex="bold"/>
        </style:style>
               """
        T2style = Style(name="T2", family="text")
        T2style.addElement(TextProperties(fontweight="bold",fontweightasian="bold",
        fontweightcomplex="bold"))
        textdoc.automaticstyles.addElement(T2style)
               
        # T5
        """
        <style:style style:name="T5" style:family="text">
        <style:text-properties fo:color="#ff0000" style:font-name="Arial"/>
        </style:style>
        """
        T5style = Style(name="T5", family="text")
        T5style.addElement(TextProperties(color="#ff0000",fontname="Arial"))
        textdoc.automaticstyles.addElement(T5style)
               
        # now construct what goes into <office:text>
               
        h=H(outlinelevel=1, text='Purpose (Heading 1)')
        textdoc.text.addElement(h)
        p = P(text="The following sections illustrate various possibilities in ODF Text", 
        stylename='Text_20_body')
        textdoc.text.addElement(p)
               
        textdoc.text.addElement(H(outlinelevel=2,text='A simple series of paragraphs    (Heading 2)'))
        textdoc.text.addElement(P(text="This section contains a series of paragraphs.",  stylename='Text_20_body'))
        textdoc.text.addElement(P(text="This is a second paragraph.", 
        stylename='Text_20_body'))
        textdoc.text.addElement(P(text="And a third paragraph.", stylename='Text_20_body'))
               
        textdoc.text.addElement(H(outlinelevel=2,text='A section with lists (Heading 2)'))
        textdoc.text.addElement(P(text="Elements to illustrate:"))
               
        # add the first list (unordered list)
        textList = List(stylename="L1")
        item = ListItem()
        item.addElement(P(text='hyperlinks', stylename="P1"))
        textList.addElement(item)
               
        item = ListItem()
        item.addElement(P(text='italics and bold text', stylename="P1"))
        textList.addElement(item)
               
        item = ListItem()
        item.addElement(P(text='lists (ordered and unordered)', stylename="P1"))
        textList.addElement(item)
               
        textdoc.text.addElement(textList)
               
        # add the second (ordered) list
               
        textdoc.text.addElement(P(text="How to figure out ODF"))
               
        textList = List(stylename="L5")
        #item = ListItem(startvalue=P(text='item 1'))
        item = ListItem()
        item.addElement(P(text='work out the content.xml tags', stylename="P5"))
        textList.addElement(item)
               
        item = ListItem()
        item.addElement(P(text='work styles into the mix', stylename="P5"))
        textList.addElement(item)
               
        item = ListItem()
        item.addElement(P(text='figure out how to apply what we learned to spreadsheets and presentations', stylename="P5"))
        textList.addElement(item)
               
        textdoc.text.addElement(textList)
               
        # A paragraph with bold, italics, font change, and hyperlinks
        """
        <text:p>The <text:span text:style-name="T1">URL</text:span> for <text:span
        text:style-name="T5">Flickr</text:span> is <text:a xlink:type="simple"
        xlink:href="http://www.flickr.com/"
        >http://www.flickr.com</text:a>. <text:s/>The <text:span
        text:style-name="T2"
        >API page</text:span> is <text:a xlink:type="simple"
        xlink:href="http://www.flickr.com/services/api/"
        >http://www.flickr.com/services/api/</text:a></text:p>
        """
        p = P(text='The ')
        # italicized URL
        s = Span(text='URL', stylename='T1')
        p.addElement(s)
        p.addText(' for ')
        # Flickr in red and Arial font
        p.addElement(Span(text='Flickr',stylename='T5'))
        p.addText(' is ')
        # link
        link = A(type="simple",href="http://www.flickr.com", text="http://www.flickr.com")
        p.addElement(link)
        p.addText('.  The ')
        # API page in bold
        s = Span(text='API page', stylename='T2')
        p.addElement(s)
        p.addText(' is ')
        link = A(type="simple",href="http://www.flickr.com/services/api", 
               text="http://www.flickr.com/services/api")
        p.addElement(link)
               
        textdoc.text.addElement(p)
               
        # add the table
        """
        <table:table-column table:number-columns-repeated="3"/>
        """
               
        textdoc.text.addElement(H(outlinelevel=1,text='A Table (Heading 1)'))
               
        table = Table(name="Table 1")
               
        table.addElement(TableColumn(numbercolumnsrepeated="3"))
               
        # first row
        tr = TableRow()
        table.addElement(tr)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='Website'))
        tr.addElement(tc)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='Description'))
        tr.addElement(tc)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='URL'))
        tr.addElement(tc)
               
        # second row
        tr = TableRow()
        table.addElement(tr)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='Flickr'))
        tr.addElement(tc)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='A social photo sharing site'))
        tr.addElement(tc)
        tc = TableCell(valuetype="string")
               
        link = A(type="simple",href="http://www.flickr.com", text="http://www.flickr.com")
        p = P()
        p.addElement(link)
        tc.addElement(p)
               
        tr.addElement(tc)
               
        # third row
        tr = TableRow()
        table.addElement(tr)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='Google Maps'))
        tr.addElement(tc)
        tc = TableCell(valuetype="string")
        tc.addElement(P(text='An online map'))
        tr.addElement(tc)
        tc = TableCell(valuetype="string")
               
        link = A(type="simple",href="http://maps.google.com", text="http://maps.google.com")
        p = P()
        p.addElement(link)
        tc.addElement(p)
        tr.addElement(tc)
               
        textdoc.text.addElement(table)
               
        # paragraph with footnote
               
        """
        <text:h text:outline-level="1">Footnotes (Heading 1)</text:h>
        <text:p>This sentence has an accompanying footnote.<text:note text:id="ftn0"
        text:note-class="footnote">
        <text:note-citation>1</text:note-citation>
        <text:note-body>
        <text:p text:style-name="Footnote">You are reading a footnote.</text:p>
        </text:note-body>
        </text:note>
        <text:s text:c="2"/>Where does the text after a footnote go?</text:p>
        """
               
        textdoc.text.addElement(H(outlinelevel=1,text='Footnotes (Heading 1)'))
        p = P()
        textdoc.text.addElement(p)
        p.addText("This sentence has an accompanying footnote.")
        note = Note(id="ftn0", noteclass="footnote")
        p.addElement(note)
        note.addElement(NoteCitation(text='1'))
        notebody = NoteBody()
        note.addElement(notebody)
        notebody.addElement(P(stylename="Footnote", text="You are reading a footnote."))
        p.addElement(S(c=2))
        p.addText("Where does the text after a footnote go?")
               
        # Insert the photo
               
        """
        <text:h text:outline-level="1">An Image</text:h>
        <text:p>
        <draw:frame draw:name="graphics1" text:anchor-type="paragraph"
        svg:width="5in"
        svg:height="6.6665in" draw:z-index="0">
        <draw:image xlink:href="Pictures/campanile_fog.jpg" xlink:type="simple"
        xlink:show="embed"
        xlink:actuate="onLoad"/>
        </draw:frame>
        </text:p>
        """
               
        #textdoc.text.addElement(H(outlinelevel=1,text='An Image'))
        #p = P()
        #textdoc.text.addElement(p)
        # add the image
        
        # img_path is the local path of the image to include
        #img_path = '[PATH-FOR-IMAGE]';
        #img_path = 'D:\Document\PersonalInfoRemixBook\examples\ch17\campanile_fog.jpg'
        #href = textdoc.addPicture(img_path)
        #f = Frame(name="graphics1", anchortype="paragraph", width="5in", height="6.6665in", 
        #zindex="0")
        #p.addElement(f)
        #img = Image(href=href, type="simple", show="embed", actuate="onLoad")
        #f.addElement(img)
               
        # save the document
        textdoc.save(fname)   
        options = {}
        connection = cups.Connection()
        connection.printFile('PDF', fname, 'DESPACHO', options=options)
virtual_report_spool()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
