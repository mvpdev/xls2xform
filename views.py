from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import SubmissionForm
from models import Submission, XForm
from xls2xform import write_xforms

def convert_file(request):
    if request.method != "POST":
        # if nothing's posted give them an empty form
        return render_to_response("upload.html", {"form": SubmissionForm()})
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
                return render_to_response("upload.html", {"msg": s.error_msg, "form": SubmissionForm()})
        else:
            # invalid forms should try uploading again
            return render_to_response("upload.html", {"form": populated_form})
