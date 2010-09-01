#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from forms import SubmissionForm
from models import Submission, XForm
import xls2xform
from xls2xform import write_xforms, ConversionError
from django.conf import settings
import markdown
import os
import codecs, pydoc, sys

def convert_file(request):
    kwargs = {"most_recent_survey" : "surveys-v0.1.xls"}

    # here's a hack to avoid dealing with serving static files
    # I've passed the responsibility to settings.py
    readme = codecs.open(settings.PATH_TO_XLS2XFORM + "README.mkdn", mode="r", encoding="utf8")
    text = readme.read()
    kwargs["documentation"] = markdown.markdown(text)

    textdoc = pydoc.TextDoc()
    kwargs["api"] = pydoc.plain( textdoc.docmodule(xls2xform) )

    kwargs["form"] = SubmissionForm()

    if request.method != "POST":
        # if nothing's posted give them an empty form
        return render_to_response("upload.html", kwargs)
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
                return render_to_response("list.html", {"list": XForm.objects.filter(submission=s)})
            except ConversionError, e:
                # record and display any error messages
                s.error_msg = e.__str__()
                s.save()
                kwargs["msg"] = s.error_msg
                return render_to_response("upload.html", kwargs)
        else:
            # invalid forms should try uploading again
            kwargs["form"] = populated_form
            return render_to_response("upload.html", kwargs)


def download_xform(request, path):
    xml_data_file = open("xls2xform/" + path, "rb").read()
    return HttpResponse(xml_data_file, mimetype="application/download")
