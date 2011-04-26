from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from main.models import XForm
from django.views.decorators.csrf import csrf_exempt
import json, re, random, os

from pyxform.xls2json import SurveyReader
from xls2xform import settings

def index(request):
    context = RequestContext(request)
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/admin/")
    context.xforms = request.user.xforms.all()
    context.title = "XLS2XForm v2.0-beta1"
    return render_to_response("index.html", context_instance=context)

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

def download_xform(request, survey_id, version_number=None, xform_file_name=None):
    context = RequestContext(request)
    user = request.user
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    if version_number is None:
        version_number = xform.latest_version.version_number
        survey_object = xform.export_survey()
        xf_filename = "%s.xml" % survey_object.id_string()
        return HttpResponseRedirect("/edit/%s/download/%s/%s" % (survey_id, version_number, xf_filename))
    else:
        survey_object = xform.export_survey()
        xf_filename = "%s.xml" % survey_object.id_string()
        xform_str = survey_object.to_xml()
        return HttpResponse(xform_str, mimetype="application/download")

@login_required()
def create_xform(request):
    """
    Starts a new, empty xform.
    """
    form_id_string = request.GET[u'id_string']
    user = request.user
    xform = XForm.objects.create(id_string=form_id_string, user=user)
    return HttpResponseRedirect("/edit/%s" % form_id_string)

def process_xls_io_to_section_json(file_io):
    file_name = file_io.name
    slug = re.sub("\.xlsx?", "", file_name)
    tmp_file_name = "%d_%s" % (random.randint(100000, 1000000), file_name)
    tmp_xls_dir = os.path.join(settings.CURRENT_DIR, "xls_tmp")
    if not os.path.exists(tmp_xls_dir): os.mkdir(tmp_xls_dir)
    
    tmp_xls_file = os.path.join(tmp_xls_dir, tmp_file_name)
    
    f = open(tmp_xls_file, 'w')
    f.write(file_io.read())
    f.close()
    
    xlr = SurveyReader(tmp_xls_file)
    xls_vals = xlr.to_dict()
    question_list = xls_vals.get(u'children')
    qjson = json.dumps(question_list)
    
    os.remove(tmp_xls_file)
    return (slug, qjson)

@login_required()
def edit_xform(request, survey_id):
    context = RequestContext(request)
    user = request.user
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    context.title = "Edit XForm - %s" % xform.id_string
    if request.method == 'POST':
        #file has been posted
        section_file = request.FILES[u'section_file']
        file_name = section_file.name
        if re.search(".json$", file_name):
            slug = re.sub(".json", "", file_name)
            section_json = section_file.read()
        elif re.search(".xlsx?$", file_name):
            slug, section_json = process_xls_io_to_section_json(section_file)
        else:
            raise Exception("This file is not understood: %s" % file_name)
        xform.add_or_update_section(slug=slug, section_json=section_json)
    context.xform = xform
    
    lv = xform.latest_version
    
    #section_portfolio:
    # --> all sections that have been uploaded to this form
    #included_base_sections:
    # --> all sections that have been specified for use in the base_section
    section_portfolio, included_base_sections = lv.all_sections()
    
    context.available_sections = section_portfolio
    context.available_sections_empty = len(section_portfolio)==0
    
    context.base_sections = included_base_sections
    context.base_sections_empty = len(included_base_sections)==0
    
    return render_to_response("edit_xform.html", context_instance=context)

@login_required()
def edit_section(request, survey_id, section_slug, action):
    user = request.user
    xform = user.xforms.get(id_string=survey_id)
    section = xform.latest_version.sections.get(slug=section_slug)
    latest_version = xform.latest_version
    section_portfolio, included_base_sections = latest_version.all_sections()
    active_slugs = [s.slug for s in included_base_sections]
    
    if action=="activate":
        xform.activate_section(section)
    elif action=="deactivate":
        xform.deactivate_section(section)
    elif action=="delete":
        xform.remove_section(slug=section_slug)
    elif action=="up":
        #move the section up one...
        ii = active_slugs.index(section_slug)
        if ii > 0:
            active_slugs.remove(section_slug)
            active_slugs.insert(ii-1, section_slug)
            xform.order_base_sections(active_slugs)
    elif action=="down":
        #move the section down one...
        ii = active_slugs.index(section_slug)
        if ii < len(active_slugs)-1:
            active_slugs.remove(section_slug)
            active_slugs.insert(ii+1, section_slug)
            xform.order_base_sections(active_slugs)
    return HttpResponseRedirect("/edit/%s" % xform.id_string)

@login_required()
def debug_json(request, survey_id):
    """
    This is for testing in early development. This returns a JSON string
    with the values that should be passed to a pyxform builder.
    """
    user = request.user
    xform = user.xforms.get(id_string=survey_id)
#    j = xform._export_survey_package()
    try:
        j = xform.export_survey(finalize=False, debug=True)
        return HttpResponse(json.dumps(j))
    except Exception, e:
        return HttpResponse(json.dumps({'error': e.__repr__()}))
