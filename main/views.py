from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from main.models import XForm

def index(request):
    context = RequestContext(request)
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/admin/")
    
    context.xforms = request.user.xforms.all()
    
#    context.xforms = request.user.
    return render_to_response("index.html", context_instance=context)

from django.views.decorators.csrf import csrf_exempt

import json
import re

@csrf_exempt
def validate_xform(request, survey_id):
    """
    This will validate the xform and save it 
    """
    context = RequestContext(request)
    user = request.user
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    
    response_dict = {'status': 'good'}
    section_errors = 0
    section_stats = {}
    for section in xform.latest_version.sections.all():
        section_response_dict = {}
        section_valid = True
        try:
            section.validate()
            section_valid = True
            section_response_dict['status'] = 'good'
        except Exception, e:
            section_response_dict['status'] = 'error'
            section_response_dict['message'] = e.__repr__()
            section_valid = False
        
        section_stats[section.slug] = section_response_dict
        if section_valid == False:
            section_errors += 1
    
    response_dict[u'section_stats'] = section_stats
    response_dict[u'section_errors'] = section_errors
    
    if section_errors == 0:
        try:
            survey_object = xform.export_survey()
            survey_object.to_xml()
        except Exception, e:
            response_dict['status'] = 'error'
            response_dict['message'] = e.__repr__()
    else:
        response_dict['status'] = 'error'
        response_dict['message'] = 'There were errors in the sections.'
    
    return HttpResponse(json.dumps(response_dict))


@csrf_exempt
def download_xform(request, survey_id):
    context = RequestContext(request)
    user = request.user
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    
    survey_object = xform.export_survey()
    xform_str = survey_object.to_xml()
    return HttpResponse(xform_str, mimetype="application/download")

def create_xform(request):
    form_id_string = request.GET[u'id_string']
    user = request.user
    
    xform = XForm.objects.create(id_string=form_id_string, user=user)
    return HttpResponseRedirect("/edit_xform/%s" % form_id_string)

def edit_xform(request, survey_id):
    context = RequestContext(request)
    user = request.user
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    if request.method == 'POST':
        #file has been posted
        new_file = request.FILES[u'new_section']
        file_name = new_file.name
        if re.search(".json$", file_name):
            slug = re.sub(".json", "", file_name)
            section_json = new_file.read()
        elif re.search(".xlsx?$", file_name):
            slug = re.sub(".xlsx?", "", file_name)
            raise NotImplementedError("Excel files not converted right now")
        else:
            raise Exception("Do not understand this file: %s" % file_name)
        xform.add_or_update_section(slug=slug, section_json=section_json)
    context.xform = xform
    context.available_sections = xform.latest_version.sections.all()
    context.base_sections = context.available_sections
    return render_to_response("edit_xform.html", context_instance=context)