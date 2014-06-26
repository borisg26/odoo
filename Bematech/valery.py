import oerplib
from oerplib import rpc
from oerplib.service.osv.browse import BrowseRecord
from oerplib.service.osv.osv import Model
import psycopg2
import sys
import fdb
import base64
class Valery():
    def productos(self):
        return None
Valery() 
if __name__ == '__main__':
    con = None
    try:
        # convesion
        caracteres = {'\xc1':'A',
             '\xc9':'E',
             '\xcd':'I',
             '\xd3':'O',
             '\xda':'U',
             '\xdc':'U',
             '\xd1':'N',
             '\xc7':'C',
             '\xed':'i',
             '\xf3':'o',
             '\xf1':'n',
             '\xe7':'c',
             '\xba':'',
             '\xb0':'',
             '\x3a':'',
             '\xe1':'a',
             '\xe2':'a',
             '\xe3':'a',
             '\xe4':'a',
             '\xe5':'a',
             '\xe8':'e',
             '\xe9':'e',
             '\xea':'e',       
             '\xeb':'e',       
             '\xec':'i',
             '\xed':'i',
             '\xee':'i',
             '\xef':'i',
             '\xf2':'o',
             '\xf3':'o',
             '\xf4':'o',   
             '\xf5':'o',
             '\xf0':'o',
             '\xf9':'u',
             '\xfa':'u',
             '\xfb':'u',               
             '\xfc':'u',
             '\xe5':'a',
             '\xf1':'n',
             '\xd1':'N',
        
        }
        con = psycopg2.connect(database='CTI-Base', user='master') 
        curSQL = con.cursor()
        curSQL.execute('SELECT version()')          
        ver = curSQL.fetchone()
        print ver
        # estamos conectado a openerp
        # intentamos conectarno con firebird
        conFb = fdb.connect(dsn='192.168.1.104:c:/valery_profesional/datos/VALERY.MDF', user='SYSDBA', password='masterkey')
        cursorDepartamentos = conFb.cursor()
        cursorProductos = conFb.cursor()
        cursorImagenes = conFb.cursor()
        #sintaxis = "SELECT  Codigo, Nombre from DEPARTAMENTOS where CODIGO='MEMORIAS' order by Nombre"
        sintaxis = "SELECT  Codigo, Nombre from DEPARTAMENTOS order by Nombre"
        cursorDepartamentos.execute(sintaxis)
        for (Codigo, Nombre) in cursorDepartamentos:
            stament = "INSERT INTO product_category (parent_left,create_uid,name,type) VALUES(0,1," + "'" + str(Nombre) + "','normal') RETURNING id "
            curSQL.execute(stament)
            con.commit()
            departamento_id = curSQL.fetchone()[0]
            el_codigo = Codigo.lstrip()
            
            #SELECT = "select Codigo_producto, Nombre_corto, Nombre, Precio_maximo from PRODUCTOS_TERMINADOS where ESTATUS = 'A' and DEPARTAMENTO_CODIGO= '" + el_codigo +"' and codigo_producto='203-133-128'   order by Nombre"
            SELECT = "select Codigo_producto, Nombre_corto, Nombre, Precio_maximo from PRODUCTOS_TERMINADOS where ESTATUS = 'A' and DEPARTAMENTO_CODIGO= '" + el_codigo +"' order by Nombre"
            cursorProductos.execute(SELECT)
            for (Codigo_producto, Nombre_corto, Nombre,Precio_maximo) in cursorProductos:
                # valido el nombre
                el_nombre_corto = Nombre_corto
                el_nombre = Nombre
                nueva_cadena = Nombre
                try:
                    for c in caracteres.keys():
                        nueva_cadena = el_nombre_corto.replace(c,caracteres[c])
                        el_nombre_corto=nueva_cadena.encode('utf-8')
                except:          
                    el_nombre_corto = 'Error en el Nombre_corto' 
                    pass
                
                try:
                    for c in caracteres.keys():
                        nueva_cadena = el_nombre.replace(c,caracteres[c])
                    el_nombre=nueva_cadena.encode('utf-8')
                except:          
                    el_nombre = 'Error en el Nombre' 
                    pass
                    

                stament = "INSERT INTO product_template (description_sale,name,description,standard_price,list_price,mes_type,uom_id,uom_po_id," \
                "type,procure_method,cost_method,categ_id,supply_method,sale_ok)  VALUES('" +Codigo_producto.lstrip()+ "','"+  el_nombre_corto.lstrip() + "','" \
                + el_nombre.lstrip() +"'," +str(Precio_maximo) +","+str(Precio_maximo)+",'fixed',1,1,'product','make_to_stock','standard'," + str(departamento_id) +",'buy',True) RETURNING id"
                #print '%s' % (stament)  
                curSQL.execute(stament)
                con.commit() 
                templateid = curSQL.fetchone()[0]
                try:
                    curSQL.execute(stament)
                    con.commit()
                    print '%s' % (el_nombre_corto)
                except psycopg2.DatabaseError, e:
                    print 'Error %s' % e                   

            #cur.execute("INSERT INTO product_product (default_code,name_template,product_tmpl_id,valuation) VALUES('" + codigo_producto) + "','" + Nombre+"',1,'manual_periodic')" )
            #con.commit()           
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
    finally:
        if con:
            con.close()    
    
    
    
    #cnt = rpc.ConnectorXMLRPC('localhost',port=8069)
    
    #oerp = oerplib.OERP('localhost',protocol='netrpc',port=8070,version='7.0')
    #oerp.login('openerp', '123', 'CTI-Base')
    #conexionvalery=None
    categorias=None
  