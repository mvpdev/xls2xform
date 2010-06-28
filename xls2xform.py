# useful piece on adding functions to xforms:
# http://groups.google.com/group/open-data-kit/browse_thread/thread/325a81f8016d618f

# xls2xform.py by Andrew Marder 6/22/2010
# a python program for translating a spreadsheet into an xform

# first set up all the key nodes for an xform
from xml.dom.minidom import Document

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
        lnode = doc.createElement("label")
        lnode.appendChild( doc.createTextNode(label ) )
        node.appendChild(lnode)

# fill in the content of the survey
# want to get the title of the survey from the sheet name
title.appendChild( doc.createTextNode("Demography Survey") )

ihead = instance
bhead = body

from xlrd import open_workbook
forms = open_workbook('forms.xls')

demography = forms.sheet_by_name('Demography')
choices = forms.sheet_by_name('Choices')

# go through each question of the demography survey updating the xform
for row in range(1,demography.nrows):
    q = {}
    for col in range(0,demography.ncols):
        q[ demography.cell(0,col).value ] = demography.cell(row,col).value

    # set up the instance
    if q['tag']:
        inode = doc.createElement( q['tag'] )
        ihead.appendChild( inode )
        ipath = path(instance,inode)
    if q['ihead']=='push':
        ihead = inode
    if q['ihead']=='pop':
        ihead = ihead.parentNode

    # set up the bindings
    bind = doc.createElement("bind")
    for attribute in ['type','relevant','required','constraint','jr:constraintMsg']:
        if q[attribute]:
            bind.setAttribute( attribute, q[attribute] )
    if bind.hasAttributes():
        bind.setAttribute( 'nodeset', ipath )
        model.appendChild( bind )

    # set up the body, this could be cleaned up a bit
    if q['controltype']:
        bnode = doc.createElement( q['controltype'] )
        bnode.setAttribute( "ref", ipath )
        addLabel( bnode, q['label'] )

        if q['choices']:
            value = 2*(int(q['choices']) - 1)
            label = value+1
            for i in range(1,choices.nrows):
                item = doc.createElement("item")
                if choices.cell(i,value).value:
                    addLabel( item, choices.cell(i,label).value )
                    item.appendChild( doc.createElement("value") ).appendChild( doc.createTextNode(choices.cell(i,value).value) )
                    bnode.appendChild(item)
        bhead.appendChild(bnode)
    elif q['group']=='push':
        bhead = bhead.appendChild( doc.createElement( "group" ) )
        addLabel( bhead, q['label'] )

        if q['repeat']=='push':
            bhead = bhead.appendChild( doc.createElement( "repeat" ) )
            bhead.setAttribute( "nodeset", ipath )

    if q['repeat']=='pop':
        bhead = bhead.parentNode
    if q['group']=='pop':
        bhead = bhead.parentNode

# id attribute required http://code.google.com/p/opendatakit/wiki/ODKAggregate
instance.firstChild.setAttribute( 'xmlns', '' )

print doc.toprettyxml(indent="  ")

quit()







