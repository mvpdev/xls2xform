from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from forms import SubmissionForm
from models import Submission, XForm
from xls2xform import write_xforms
from django.conf import settings

import os

def convert_file(request):
	most_recent_survey = "surveys00.xls"
	if request.method != "POST":
		# if nothing's posted give them an empty form
		return render_to_response("upload.html", {"form": SubmissionForm(), "most_recent_survey": most_recent_survey})
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
			except Exception, e:
				# record and display any error messages
				s.error_msg = e.args[0]
				s.save()
				return render_to_response("upload.html", {"msg": s.error_msg, "form": SubmissionForm(), "most_recent_survey": most_recent_survey})
		else:
			# invalid forms should try uploading again
			return render_to_response("upload.html", {"form": populated_form, "most_recent_survey": most_recent_survey})


def download_xform(request, path):
	xml_data_file = open("%sxls2xform/%s" % (settings.MEDIA_ROOT, path), "rb").read()
	return HttpResponse(xml_data_file, mimetype="application/download")
