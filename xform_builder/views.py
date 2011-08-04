import json
import os
import re

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
from django.template.defaultfilters import slugify as django_slugify

from xform_builder.models import XForm
from pyxform.xls2json import SurveyReader
from pyxform.builder import create_survey_from_path
from xls2xform import settings
from original_xls2xform import write_xforms


def slugify(str):
    return re.sub("-", "_", django_slugify(str))


class QuickConverter(forms.Form):
    xls_file = forms.FileField(label="XLS File")
    original_syntax = forms.BooleanField(
        required=False,
        help_text="Check this box if you are using the orginal xls2xform syntax. If you didn't know there were two different versions of xls2xform, leave this box unchecked."
        )

    def _get_xforms_using_original_xls2xform(self):
        """
        Try using the original xls2xform script. If there is an
        exception return the exception, otherwise return a dictionary
        where the keys are the filenames and the values are the xml of
        the corresponding xform. todo: we need to delete the files
        created by write_xforms.
        """
        try:
            xforms = write_xforms(self.path)
        except Exception as e:
            return e
        result = {}
        for xform in xforms:
            with open(xform, "r") as f:
                file_name = os.path.basename(xform)
                result[file_name] = f.read()
        return result

    def _get_xform_using_pyxform(self):
        """
        Try using pyxform to convert the xls file into an xform. If
        there is an exception return the exception, otherwise return a
        dictionary where the single key is the desired file name and
        the value is the xml of the xform.
        """
        try:
            survey = create_survey_from_path(self.path)
            xform_str = survey.to_xml()
        except Exception as e:
            return e
        file_name = survey.id_string() + ".xml"
        return {file_name: xform_str}

    def get_xforms(self):
        """
        Try using both the old and new conversion methods on the
        passed in xls file. If the new method works return the
        resulting xform. If the old method works return the resulting
        xform. Otherwise throw the exception from the new method. It
        would be better to give the exception from both methods.
        """
        xls = self.cleaned_data['xls_file']
        self.path = save_in_temp_dir(xls)

        old = self._get_xforms_using_original_xls2xform()
        new = self._get_xform_using_pyxform()
        os.remove(self.path)

        if type(new) is dict:
            return self._package(new)
        elif type(old) is dict:
            return self._package(old)
        else:
            if self.cleaned_data['original_syntax']:
                raise old
            else:
                raise new

    def _package(self, d):
        assert len(d) == 1, "Code only supports single XForms."
        filename = d.keys()[0]
        response = HttpResponse(d[filename], mimetype="application/download")
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response


def quick_converter(request):
    if request.method == 'POST':
        form = QuickConverter(request.POST, request.FILES)
        if form.is_valid():
            return form.get_xforms()
    else:
        form = QuickConverter()
    context = RequestContext(request)
    context.form = form
    return render_to_response(
        'quick_converter.html', context_instance=context
        )


class CreateXForm(forms.Form):
    title = forms.CharField()
    id_string = forms.CharField(help_text="The ID string is used internally to link submissions to this survey.")

    def clean_id_string(self):
        id_string = slugify(self.data.get(u'id_string'))
        user = self.data.get(u'user')
        existing_forms = XForm.objects.filter(id_string=id_string,
                     user=user).count()
        if existing_forms > 0:
            raise forms.ValidationError("You already have a form with this ID string: %s" % id_string)
        return id_string


def home(request):
    if request.user.is_authenticated():
        return index(request)
    else:
        return quick_converter(request)


@login_required
def index(request):
    context = RequestContext(request)
    context.title = "XLS2XForm v2.0-beta1"
    context.form = CreateXForm()
    context.page_name = "Home"

    if request.method == "POST":
        id_string = request.POST.get(u'id_string')
        title = request.POST.get(u'title')

        submitted_form = CreateXForm({
            'id_string': id_string,
            'title': title,
            'user': request.user
        })
        if submitted_form.is_valid():
            xf_data = submitted_form.cleaned_data
            xf_data['user'] = request.user
            xf = XForm.objects.create(**xf_data)
            return HttpResponseRedirect("/edit/%s" % xf.id_string)
        else:
            #passed back to the page to display errors.
            context.form = submitted_form
    context.xforms = request.user.xforms.all()
    return render_to_response("index.html", context_instance=context)

def delete_xform(request, survey_id):
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    xform.delete()
    return HttpResponseRedirect("/")

def download_xform(request, survey_id, format):
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    survey_object = xform.export_survey()
    xf_filename = "%s.%s" % (survey_object.id_string(), format)
    if format == 'xml':
        xform_str = survey_object.to_xml()
    elif format == 'json':
        xform_str = json.dumps(survey_object.to_dict())
    else:
        raise Exception("Unknown file format", format)
    response = HttpResponse(xform_str, mimetype="application/download")
    response['Content-Disposition'] = 'attachment; filename=%s' % xf_filename
    return response


def convert_file_to_json(file_io):
    file_name = file_io.name
    if re.search("\.json$", file_name):
        slug = re.sub(".json$", "", file_name)
        section_json = file_io.read()
    elif re.search("\.xls$", file_name):
        slug, section_json = process_xls_io_to_section_json(file_io)
    else:
        raise Exception("This file is not understood: %s" % file_name)
    return (slug, section_json)


def save_in_temp_dir(file_io):
    file_name = file_io.name
    tmp_xls_dir = os.path.join(settings.CURRENT_DIR, "xls_tmp")
    if not os.path.exists(tmp_xls_dir):
        os.mkdir(tmp_xls_dir)
    path = os.path.join(tmp_xls_dir, file_name)
    f = open(path, 'w')
    f.write(file_io.read())
    f.close()
    return path


def process_xls_io_to_section_json(file_io):
    # I agree that this function is not pretty, but I don't think we
    # should move this into the model because I prefer to think of the
    # model as file-format independent.
    path = save_in_temp_dir(file_io)
    m = re.search(r'([^/]+).xls$', path)
    slug = m.group(1)
    xlr = SurveyReader(path)
    xls_vals = xlr.to_dict()
    qjson = json.dumps(xls_vals)
    os.remove(path)
    return (slug, qjson)


@login_required
def edit_xform(request, survey_id):
    context = RequestContext(request)
    xforms = request.user.xforms
    xform = xforms.get(id_string=survey_id)
    context.page_name = "Edit - %s" % xform.title
    context.title = "Edit XForm - %s" % xform.title
    if request.method == 'POST':
        #file has been posted
        section_file = request.FILES[u'section_file']
        slug, section_json = convert_file_to_json(section_file)
        xform.add_or_update_section(slug=slug, section_json=section_json)

        #should we auto add this section if it's the first?
#        if xform.latest_version.sections.count()==1:
#            xform.order_base_sections([form_id_string])
    context.xform = xform

    lv = xform.latest_version

    #section_portfolio:
    # --> all sections that have been uploaded to this form
    #included_base_sections:
    # --> all sections that have been specified for use in the base_section
    section_portfolio, included_base_sections = lv.all_sections()

    context.available_sections = section_portfolio
    context.available_sections_empty = len(section_portfolio) == 0

    context.base_sections = included_base_sections
    context.base_sections_empty = len(included_base_sections) == 0

    return render_to_response("edit_xform.html", context_instance=context)


@login_required
def edit_section(request, survey_id, section_slug, action):
    user = request.user
    xform = user.xforms.get(id_string=survey_id)
    section = xform.latest_version.sections.get(slug=section_slug)
    latest_version = xform.latest_version
    section_portfolio, included_base_sections = latest_version.all_sections()
    active_slugs = [s.slug for s in included_base_sections]

    if action == "activate":
        xform.activate_section(section)
    elif action == "deactivate":
        xform.deactivate_section(section)
    elif action == "delete":
        xform.remove_section(slug=section_slug)
    elif action == "up":
        #move the section up one...
        ii = active_slugs.index(section_slug)
        if ii > 0:
            active_slugs.remove(section_slug)
            active_slugs.insert(ii - 1, section_slug)
            xform.order_base_sections(active_slugs)
    elif action == "down":
        #move the section down one...
        ii = active_slugs.index(section_slug)
        if ii < len(active_slugs) - 1:
            active_slugs.remove(section_slug)
            active_slugs.insert(ii + 1, section_slug)
            xform.order_base_sections(active_slugs)
    return HttpResponseRedirect("/edit/%s" % xform.id_string)

