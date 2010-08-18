# useful piece on adding functions to xforms:
# http://groups.google.com/group/open-data-kit/browse_thread/thread/325a81f8016d618f

# learn how to handle languages
# acknowledgements
# gps, bar code scanner, photos, ...
# review widget

# xls2xform.py by Andrew Marder 6/22/2010
# a python program for translating a spreadsheet into an xform

import re
import sys
from xlrd import open_workbook
from xml.dom.minidom import Document, parseString

workbook = open_workbook( sys.argv[1] )

# set up dictionary of multiple choice lists
# the first row has the column headers
s = workbook.sheet_by_name('Choices')
choices = {}
for row in range(1,s.nrows):
    c = {}
    for col in range(0,s.ncols):
        c[s.cell(0,col).value] = s.cell(row,col).value
    list_name = c.pop("list name")
    if list_name in choices:
        choices[list_name].append(c)
    else:
        choices[list_name] = [c]

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
        title.appendChild( doc.createTextNode(sheet.name) )

        ihead = instance
        bhead = body

        # go through each question of the survey updating the xform
        for row in range(1,sheet.nrows):
            q = {}
            for col in range(0,sheet.ncols):
                label = sheet.cell(0,col).value
                value = sheet.cell(row,col).value
                if value:
                    q[label] = value

            command = q.pop("command")

            if "tag" in q:
                tag = q.pop("tag")
                assert not re.search(r"\s", tag), "Instance tags may not contain white space: " + tag
                inode = doc.createElement(tag)
                ihead.appendChild( inode )
                ipath = path(instance,inode)

            m = re.search(r"(begin|end) (survey|group|repeat)", command)
            if m:
                w = m.groups()
                if w[0]=="begin":
                    ihead = inode
                    if w[1] in ["group", "repeat"]:
                        bhead = bhead.appendChild(doc.createElement("group"))
                        # bhead.setAttribute("ref", ipath)
                        addLabel(bhead, q["label"])
                        if w[1]=="repeat":
                            bhead = bhead.appendChild(doc.createElement("repeat"))
                            bhead.setAttribute("nodeset", ipath)
                if w[0]=="end":
                    ihead = ihead.parentNode
                    if w[1]=="group":
                        bhead = bhead.parentNode
                    if w[1]=="repeat":
                        bhead = bhead.parentNode.parentNode
            else:
                m = re.search(r"^q (string|select|select1|int|geopoint|decimal|date|picture|note)( (.*))?$", command)
                assert m, "Unrecognized command: " + command
                w = m.groups()
                label = q.pop("label")

                bind = doc.createElement("bind")
                if w[0]=="note":
                    bind.setAttribute("type", "string")
                    bind.setAttribute("readonly", "true()")
                elif w[0]=="picture":
                    bind.setAttribute("type", "binary")
                else:
                    bind.setAttribute("type", w[0])
                for attribute in q.keys():
                    bind.setAttribute(attribute, q[attribute])
                bind.setAttribute("nodeset", ipath)
                model.appendChild(bind)

                control_type = {"string"   : "input",
                                "int"      : "input",
                                "geopoint" : "input",
                                "decimal"  : "input",
                                "date"     : "input",
                                "note"     : "input",
                                "select"   : "select",
                                "select1"  : "select1",
                                "picture"  : "upload",}
                bnode = doc.createElement(control_type[w[0]])
                if w[0]=="picture":
                    bnode.setAttribute("mediatype", "image/*")
                bnode.setAttribute("ref", ipath)
                addLabel(bnode, label)
                bhead.appendChild(bnode)

                if w[0] in ["select", "select1"]:
                    for c in choices[w[2]]:
                        v = str(c["value"])
                        item = doc.createElement("item")
                        addLabel(item, c["label"])
                        assert not re.search("\s", v), "Multiple choice values are not allowed to have spaces: " + v
                        item.appendChild(doc.createElement("value")).appendChild(doc.createTextNode(v))
                        bnode.appendChild(item)


        # id attribute required http://code.google.com/p/opendatakit/wiki/ODKAggregate
        instance.firstChild.setAttribute( 'id', sheet.name )

        f = open(sheet.name + '.xml', 'w')
        # f.write( doc.toprettyxml(indent="  ").encode('utf-8') )
        f.write( doc.toxml().encode('utf-8') )
        f.close()

quit()







