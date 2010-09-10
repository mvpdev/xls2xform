#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""A Python script to convert properly formatted excel files into
XForms for use with Open Data Kit."""

import os, re, sys
from xlrd import open_workbook
from xml.dom.minidom import Document, parseString

class ConversionError(Exception):
    def __init__(self, type, info):
        self.type = type
        self.info = info

    def __str__(self):
        return u"%(type)s: %(info)s" % self.__dict__

def xpath(a, b):
    """Return the XPath from node a to node b, assumes b is a descendant
    of a."""
    if a.isSameNode(b):
        return ""
    return xpath(a, b.parentNode) + "/" + b.localName

def add_label(xml_str, node):
    """Add a label to node's list of children, the XML contained in
    that label comes from xml_str.

    We want to make referencing variables easier, maybe using
    $varname."""
    if xml_str:
        s = u'<?xml version="1.0" ?><label>' + xml_str + u"</label>"
        node.appendChild( parseString(s.encode("utf-8")).documentElement )

def construct_choice_lists(sheet):
    """Return a dictionary of multiple choice lists from the Excel
    Worksheet 'sheet'.

    The Worksheet named 'Select Choices' defines the choices for
    all multiple choice questions. This sheet must have three
    columns with the following headers: 'list name', 'value', and
    'label'. Each row below the columns headers describes a single
    choice option, the value in the 'list name' column is the name
    of the list of multiple choice options that this option
    belongs to. The 'value' column specifies the value that will
    be stored in the database when this option is chosen, and the
    'label' column is what the surveyor will see on the phone's
    screen."""
    d = {}
    for row in range(1,sheet.nrows):
        c = {}
        for col in range(0,sheet.ncols):
            c[sheet.cell(0,col).value] = sheet.cell(row,col).value
        list_name = c.pop("list name")
        if list_name in d:
            d[list_name].append(c)
        else:
            d[list_name] = [c]
    return d


def write_xforms(xls_file_path):
    """Convert a properly formatted excel file into XForms for use with
    Open Data Kit. Return a list of all the XForms created.

    begin_command ::= begin (survey|group|repeat)
    end_command ::= end (survey|group|repeat)
    q_command ::= q (string|int|geopoint|decimal|date|picture|note|select_choices)
    select_choices ::= (select|select1) list_name

    We do not support multiple languages yet, but we will."""
    xforms = []

    workbook = open_workbook(xls_file_path)
    folder = os.path.dirname(xls_file_path)

    choice_sheet = "Select Choices"
    choices = construct_choice_lists( workbook.sheet_by_name(choice_sheet) )

    for sheet in workbook.sheets():
        if sheet.name != choice_sheet:

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

            # fill in the content of the survey
            # want to get the title of the survey from the sheet name
            title.appendChild( doc.createTextNode(sheet.name) )

            ihead = instance
            bhead = body

            control_stack = []
            tag_xpath = {}

            # go through each question of the survey updating the xform
            for row in range(1,sheet.nrows):
                q = {}
                for col in range(0,sheet.ncols):
                    label = sheet.cell(0,col).value.lower()
                    value = sheet.cell(row,col).value
                    if value:
                        q[label] = value
                command = q.pop("command", "")

                # skip blank commands
                if not command:
                    continue

                if "tag" in q:
                    tag = q.pop("tag")
                    if tag in tag_xpath:
                        raise ConversionError("Tags are used to uniquely identify survey elements. Duplicate tag", tag)
                    # http://www.w3.org/TR/REC-xml/
                    name_start_char = r"[a-zA-Z:_]"
                    name_char = name_start_char + r"|[0-9\-\.]"
                    name = "^%(start)s(%(char)s)*$" % {"start" : name_start_char, "char" : name_char}
                    m = re.search(name, tag)
                    if not m:
                        raise ConversionError(u"Invalid tag. Tags may contain upper and lowercase letters, colons, and underscores. After the first character, numbers, dashes, and periods are also accepted", tag)
                    inode = doc.createElement(tag)
                    ihead.appendChild( inode )
                    ixpath = xpath(instance,inode)
                    tag_xpath[tag] = ixpath

                m = re.search(r"(begin|end) (survey|group|repeat)", command)
                if m:
                    w = m.groups()
                    if w[0]=="begin":
                        control_stack.append(w[1])
                        ihead = inode
                        if w[1] in ["group", "repeat"]:
                            bhead = bhead.appendChild(doc.createElement("group"))
                            bhead.setAttribute("ref", ixpath)
                            add_label(q["label"], bhead)
                            if w[1]=="repeat":
                                bhead = bhead.appendChild(doc.createElement("repeat"))
                                bhead.setAttribute("nodeset", ixpath)
                    if w[0]=="end":
                        control_top = control_stack.pop()
                        if w[1]!=control_top:
                            raise ConversionError("begin " + control_top + " ended with " + w[1], ihead.localName)
                        ihead = ihead.parentNode
                        if w[1]=="group":
                            bhead = bhead.parentNode
                        if w[1]=="repeat":
                            bhead = bhead.parentNode.parentNode
                else:
                    m = re.search(r"^q (string|select|select1|int|geopoint|decimal|date|picture|note)( (.*))?$", command)
                    if not m:
                        raise ConversionError(u"Unrecognized command", command)
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

                    skippable = q.pop("skippable", None)
                    if not skippable:
                        bind.setAttribute("required", "true()")

                    for attribute in q.keys():
                        # right now we're not supporting any binding attributes
                        supported_attributes = []
                        if attribute in supported_attributes:
                            bind.setAttribute(attribute, q[attribute])
                    bind.setAttribute("nodeset", ixpath)
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
                    bnode.setAttribute("ref", ixpath)
                    add_label(label, bnode)
                    bhead.appendChild(bnode)

                    if w[0] in ["select", "select1"]:
                        if w[2] not in choices:
                            raise ConversionError("No multiple choice list named", "'%(name)s'" % {"name" : w[2]})
                        for c in choices[w[2]]:
                            v = str(c["value"])
                            item = doc.createElement("item")
                            add_label(c["label"], item)
                            if re.search("\s", v):
                                raise ConversionError(u"Multiple choice values are not allowed to have spaces", v)
                            item.appendChild(doc.createElement("value")).appendChild(doc.createTextNode(v))
                            bnode.appendChild(item)


            # id attribute required http://code.google.com/p/opendatakit/wiki/ODKAggregate
            if instance.firstChild:
                instance.firstChild.setAttribute( "id", sheet.name )
            else:
                raise ConversionError(u"Worksheet never called the begin survey command", sheet.name)

            outfile = os.path.join(folder, re.sub(r"\s+", "_", sheet.name) + ".xml")
            f = open(outfile, "w")
            # f.write( doc.toprettyxml(indent="  ").encode("utf-8") )
            f.write( doc.toxml().encode("utf-8") )
            f.close()
            xforms.append(outfile)
    return xforms

# call write_xforms on the absolute path of the excel file passed as
# an argument
if len(sys.argv)==2 and sys.argv[0]=="xls2xform.py":
    write_xforms(os.path.join(os.getcwd(), sys.argv[1]))


# NOTES:
# useful piece on adding functions to xforms:
# http://groups.google.com/group/open-data-kit/browse_thread/thread/325a81f8016d618f
