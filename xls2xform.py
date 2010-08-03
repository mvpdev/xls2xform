# useful piece on adding functions to xforms:
# http://groups.google.com/group/open-data-kit/browse_thread/thread/325a81f8016d618f

# learn how to handle languages
# acknowledgements
# gps, bar code scanner, photos, ...
# review widget

# xls2xform.py by Andrew Marder 6/22/2010
# a python program for translating a spreadsheet into an xform

import sys
from xlrd import open_workbook
workbook = open_workbook( sys.argv[1] )

# first set up all the key nodes for an xform
from xml.dom.minidom import Document, parseString

choices = workbook.sheet_by_name('Choices')
for sheet in workbook.sheets():
    if sheet.name != 'Choices':

        doc = Document()

        html = doc.createElement("h:html")
        html.setAttribute( "xmlns"     , "http://www.w3.org/2002/xforms"     )
        html.setAttribute( "xmlns:h"   , "http://www.w3.org/1999/xhtml"      )
        html.setAttribute( "xmlns:ev"  , "http://www.w3.org/2001/xml-events" )
        html.setAttribute( "xmlns:xsd" , "http://www.w3.org/2001/XMLSchema"  )
        html.setAttribute( "xmlns:jr"  , "http://openrosa.org/javarosa"      )

        head     = doc.createElement("h:head")
        title    = doc.createElement("h:title")
        model    = doc.createElement("model")
        instance = doc.createElement("instance")
        body     = doc.createElement("h:body")

        # put the nodes together
        # html: (head: (title, model: (instance)), body)
        doc.appendChild(html)
        html.appendChild(head)
        html.appendChild(body)
        head.appendChild(title)
        head.appendChild(model)
        model.appendChild(instance)

        def path(a,b):
        # Return the xpath from node a to node b
            if a.isSameNode(b):
                return ''
            return path(a,b.parentNode) + '/' + b.localName

        def addLabel(node,label):
            if label:
                if label[0:5]=="XML: ":
                    xmlstr = '<?xml version="1.0" ?><label>' + label[5:] + '</label>'
                    node.appendChild( parseString(xmlstr).documentElement )
                else:
                    lnode = doc.createElement("label")
                    lnode.appendChild( doc.createTextNode(label ) )
                    node.appendChild(lnode)

        # fill in the content of the survey
        # want to get the title of the survey from the sheet name
        title.appendChild( doc.createTextNode(sheet.name + ' Survey') )

        ihead = instance
        bhead = body

        # go through each question of the survey updating the xform
        for row in range(2,sheet.nrows):
            q = {}
            for col in range(0,sheet.ncols):
                category = sheet.cell(0,col).value     # instance, binding, or control
                field = sheet.cell(1,col).value        # specific information on setting up the instance, binding, or control
                value = sheet.cell(row,col).value      # for this question the value of the field

                if category not in q:
                    q[category] = {}

                if value:
                    q[category][field] = value
        
            # set up the instance
            if 'tag' in q['instance']:
                inode = doc.createElement( q['instance']['tag'] )
                ihead.appendChild( inode )
                ipath = path(instance,inode)
            if 'ihead' in q['instance'] and q['instance']['ihead']=='push':
                ihead = inode
            if 'ihead' in q['instance'] and q['instance']['ihead']=='pop':
                ihead = ihead.parentNode

            # set up the bindings
            if 'nodeset' in q['binding']:
                ipath=q['binding']['nodeset']

            bind = doc.createElement("bind")
            bindAttributes = q['binding']
            for attribute in bindAttributes.keys():
                bind.setAttribute( attribute, bindAttributes[attribute] )
            if bind.hasAttributes():
                bind.setAttribute( 'nodeset', ipath )
                model.appendChild( bind )

            # set up the body, this could be cleaned up a bit
            if 'type' in q['control']:
                bnode = doc.createElement( q['control']['type'] )
                if q['control']['type']=='upload':
                    bnode.setAttribute( 'mediatype', 'image/*' )
                if 'ref' in q['control']:
                    bnode.setAttribute( "ref", q['control']['ref'] )
                else:
                    bnode.setAttribute( "ref", ipath )
                addLabel( bnode, q['control']['label'] )

                if 'choices' in q['control']:
                    value = 2*(int(q['control']['choices']) - 1)
                    label = value+1
                    for i in range(1,choices.nrows):
                        item = doc.createElement("item")
                        if choices.cell(i,value).value:
                            addLabel( item, choices.cell(i,label).value )
                            item.appendChild( doc.createElement("value") ).appendChild( doc.createTextNode(str( choices.cell(i,value).value )) )
                            bnode.appendChild(item)
                bhead.appendChild(bnode)
            elif 'group' in q['control'] and q['control']['group']=='push':
                bhead = bhead.appendChild( doc.createElement( "group" ) )
                bhead.setAttribute( "ref", ipath )
                addLabel( bhead, q['control']['label'] )

                if 'repeat' in q['control'] and q['control']['repeat']=='push':
                    bhead = bhead.appendChild( doc.createElement( "repeat" ) )
                    bhead.setAttribute( "nodeset", ipath )

            if 'repeat' in q['control'] and q['control']['repeat']=='pop':
                bhead = bhead.parentNode
            if 'group' in q['control'] and q['control']['group']=='pop':
                bhead = bhead.parentNode

        # id attribute required http://code.google.com/p/opendatakit/wiki/ODKAggregate
        instance.firstChild.setAttribute( 'id', sheet.name )

        f = open(sheet.name + '.xml', 'w')
        # f.write( doc.toprettyxml(indent="  ").encode('utf-8') )
        f.write( doc.toxml().encode('utf-8') )
        f.close()

quit()







