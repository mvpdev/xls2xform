#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from forms import SubmissionForm
from models import Submission, XForm
import xls2xform
from xls2xform import write_xforms, ConversionError
from django.conf import settings
import markdown
import os
import codecs, pydoc, sys
from xlrd import XLRDError

def convert_file(request):
    context = RequestContext(request, {"most_recent_survey" : "surveys-v0.2.xls"})

    # here's a hack to avoid dealing with serving static files
    # I've passed the responsibility to settings.py
    CURRENT_FILE = os.path.abspath(__file__)
    CURRENT_DIR = os.path.dirname(CURRENT_FILE)
    path_to_readme = os.path.join(CURRENT_DIR, "README.mkdn")
    readme = codecs.open(path_to_readme, mode="r", encoding="utf8")
    text = readme.read()
    context.documentation = markdown.markdown(text)

    textdoc = pydoc.TextDoc()
    context.api = pydoc.plain( textdoc.docmodule(xls2xform) )

    context.form = SubmissionForm()

    if request.method != "POST":
        # if nothing's posted give them an empty form
        return render_to_response("upload.html", context_instance=context)
    else:
        # otherwise pull the data out of the request and process it
        populated_form = SubmissionForm(request.POST, request.FILES)
        if populated_form.is_valid():
            s = populated_form.save()
            try:
                # process the excel file
                surveys = write_xforms(s.file.path)
                for survey in surveys:
                    x = XForm(submission=s, file=survey)
                    x.save()
                # list the files created
                context.list = XForm.objects.filter(submission=s)
                return render_to_response("list.html", context_instance=context)
            except ConversionError, e:
                # record and display any error messages
                s.error_msg = e.__str__()
                s.save()
                context["msg"] = s.error_msg
                return render_to_response("upload.html", context_instance=context)
            except XLRDError, e:
                if e.__str__().startswith("Unsupported format, or corrupt file"):
                    s.error_msg = "xls2xform only accepts Excel 97 - 2004 Workbooks (.xls)"
                    s.save()
                    context["msg"] = s.error_msg
                    return render_to_response("upload.html", context_instance=context)
                else:
                    raise e                    
        else:
            # invalid forms should try uploading again
            context["form"] = populated_form
            return render_to_response("upload.html", context_instance=context)


def download_xform(request, path):
    xml_data_file = open("xls2xform/" + path, "rb").read()
    return HttpResponse(xml_data_file, mimetype="application/download")
