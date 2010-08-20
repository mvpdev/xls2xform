from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import UploadFileForm
from models import Submission

def convert_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            d = {'file' : request.FILES['file'],
                 'error_msg' : ''}
            s = Submission(**d)
            s.save()
            return HttpResponseRedirect('/files/')
    else:
        form = UploadFileForm()
    return render_to_response('upload.html', {'form': form})
