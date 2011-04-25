from django.db import models

from django.contrib.auth.models import User

import pyxform
import json

class XForm(models.Model):
    id_string = models.CharField(max_length=32)
    latest_version = models.ForeignKey('XFormVersion', null=True, related_name="active_xform")
    user = models.ForeignKey(User, related_name="xforms")
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    def __init__(self, *args, **kwargs):
        sections = kwargs.pop(u'sections', [])
        super(XForm, self).__init__(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        super(XForm, self).save(*args, **kwargs)
        if self.latest_version is None:
            self.latest_version = XFormVersion.objects.create(xform=self)
            self.save()
    
    def export_survey(self):
        latest_version = self.latest_version
        survey = pyxform.Survey(name=unicode(self.id_string))
        for s in latest_version.sections.all():
            section_json = s.section_json
            section_array = json.loads(section_json)
            for section_dict in section_array:
                survey_elem = pyxform.create_survey_element_from_dict(section_dict)
                survey.add_child(survey_elem)
        return survey
    
    def _export_survey_sections(self):
        lv = self.latest_version
        _base = json.loads(lv.base_section.section_json)
        sj = {u'_base': _base}
        sections = self.latest_version.sections.all()
        for s in sections: sj[s.slug] = json.loads(s.section_json)
        return sj
    
    def _export_survey_package(self):
        lv = self.latest_version
        base_section = lv.base_section
        try:
            surv_json = {'name': self.id_string, 'question_types':[], 'survey': \
                    base_section.gather_includes([], lv.sections_by_slug())}
        except IncludeNotFound, e:
            surv_json = {'error': e.__repr__()}
        return surv_json
    
    def validate(self):
        pass
    
    def add_or_update_section(self, *args, **kwargs):
        """
        Automatically creates a new version whenever updating one of the sections.
        """
        slug = kwargs.get(u'slug')
        
        lv = self.latest_version
        slug_dict = lv.sections_by_slug()
        new_section = XFormSection(*args, **kwargs)
        
        if slug in slug_dict.keys():
            #TODO: check to see if the new section contains changes
            #assuming not--
            remove_section = slug_dict[slug]
        else:
            remove_section = None
        
        nv = lv._clone()
        nv.sections.remove(remove_section)
        
        new_section.save()
        nv.sections.add(new_section)
        
        self.latest_version = nv
        self.save()
        return nv
    
    def remove_section(self, *args, **kwargs):
        slug = kwargs.get(u'slug', None)
        lv = self.latest_version
        matching_section = lv.sections.get(slug=slug)
        if matching_section is None: return lv
        
        slugs = lv.base_section_slugs()
        if slug in slugs:
            slugs.remove(slug)
            nv = self.order_base_sections(slugs)
            nv.sections.remove(matching_section)
        else:
            nv = lv._clone()
            nv.sections.remove(matching_section)
            self.latest_version = nv
            self.save()
    
    def activate_section(self, section):
        """
        Adds this section to the "base_section".
        """
        section_slug = section.slug
        slugs = self.latest_version.base_section_slugs()
        if section_slug not in slugs:
            slugs.append(section_slug)
            self.order_base_sections(slugs)
    
    def deactivate_section(self, section):
        """
        Removes this section from the "base_section".
        """
        section_slug = section.slug
        slugs = self.latest_version.base_section_slugs()
        if section_slug in slugs:
            slugs.remove(section_slug)
            self.order_base_sections(slugs)
    
    def order_base_sections(self, slug_list):
        """
        This sets the order of the sections included in the base_section.
        This will automatically handle "activation" of all the sections.
        """
        v = self.latest_version._clone()
        new_base = v.base_section
        slug_list_includes = []
        for slug in slug_list:
            slug_list_includes.append({u'type': u'include', u'name': slug})
        new_base.section_json = json.dumps(slug_list_includes)
        new_base.save()
        v.save()
        self.latest_version = v
        self.save()
        return v

class XFormVersion(models.Model):
    xform = models.ForeignKey(XForm, related_name="versions")
    date_created = models.DateTimeField(auto_now_add=True)
    base_section = models.ForeignKey('XFormSection', null=True)
    _included_sections = None
    
    def __init__(self, *args, **kwargs):
        base_section_json = kwargs.pop(u'base_section_json', u'[]')
        base_section = XFormSection.objects.create(section_json=base_section_json, slug="_base")
        kwargs[u'base_section'] = base_section
        super(XFormVersion, self).__init__(*args, **kwargs)
    
    def _clone(self):
        bsj = self.base_section.section_json
        new_version = XFormVersion.objects.create(base_section_json=bsj, xform=self.xform)
        for s in self.sections.all(): new_version.sections.add(s)
        return new_version
    
    def sections_by_slug(self):
        sections = {}
        for s in self.sections.all(): sections[s.slug] = s
        return sections
    
    def base_section_slugs(self):
        j_arr = json.loads(self.base_section.section_json)
        slugs = []
        for j in j_arr:
            s = j.get(u'type', None)
            if s == 'include':
                include_slug = j.get(u'name')
                slugs.append(include_slug)
        return slugs
    
    def included_base_sections(self):
        if self._included_sections is None:
            section_includes = json.loads(self.base_section.section_json)
            sections = []
            for incl in section_includes:
                itype = incl.get(u'type', None)
                if itype == 'include':
                    sect_slug = incl.get(u'name', None)
                    if sect_slug is not None: sections.append(self.sections.get(slug=sect_slug))
            self._included_sections = sections
        return self._included_sections
    
    def all_sections(self):
        included_sections = self.included_base_sections()
        available_section_list = list(self.sections.all())
        for s in available_section_list: s.is_marked_included = s in self._included_sections
        return (available_section_list, self._included_sections)
        
class SectionIncludeError(Exception):
    def __init__(self, container, include_slug):
        self.container = container
        self.include_slug = include_slug

class IncludeNotFound(SectionIncludeError):
    def __repr__(self):
        return "The section '%s' was not able to include the section '%s'" % \
                    (self.container, self.include_slug)
    
class CircularInclude(SectionIncludeError):
    def __repr__(self):
        return "The section '%s' detected a circular include of section '%s'" % \
                    (self.container, self.include_slug)

import copy

class XFormSection(models.Model):
    slug = models.CharField(max_length=32)
    section_json = models.TextField()
    versions = models.ManyToManyField("XFormVersion", related_name="sections")
    is_marked_included = False
    _sub_sections = None
    
    def __init__(self, *args, **kwargs):
        """
        converts a section_dict argument to json.
        """
        d = kwargs.pop(u'section_dict', kwargs.pop('section_dict', None))
        if d is not None: kwargs[u'section_json'] = json.dumps(d)
        return super(XFormSection, self).__init__(*args, **kwargs)
    
    def sub_sections(self):
        if self._sub_sections is None:
            self._sub_sections = []
            sd = json.loads(self.section_json)
            for d in sd:
                if d.get(u'type')=='include': self._sub_sections.append(d.get(u'name'))
                if d.get(u'type') in ['repeat', 'loop', 'group']:
                    for aa in d.get(u'children'):
                        if aa.get(u'type')=='include': self._sub_sections.append(aa.get(u'name'))
        return self._sub_sections
    
    def gather_includes(self, oput, portfolio, include_stack=[]):
        """
        This will ideally just add included sections to a list rather than
        nesting an array that gets returned...
        """
        section_list = json.loads(self.section_json)
        for qqq in section_list:
            qqqtype = qqq.get(u'type', None)
            if qqqtype=='include':
                include_section = qqq.get(u'name', None)
                if include_section not in portfolio:
                    raise IncludeNotFound(self.slug, include_section)
                if include_section in include_stack:
                    raise CircularInclude(self.slug, include_section)
                
                bl = copy.copy(include_stack)
                bl.append(include_section)
                section = portfolio.get(include_section)
                section.gather_includes(oput, portfolio, bl)
            else:
                oput.append(qqq)
        return oput
    
    def _questions_list(self):
        return json.loads(self.section_json)

    def validate(self):
        survey = pyxform.Survey(name="section_test")
        section_array = json.loads(self.section_json)
        for section_dict in section_array:
            survey_elem = pyxform.create_survey_element_from_dict(section_dict)
            survey.add_child(survey_elem)
        xml = survey.to_xml()
        raise Exception("THERE WAS A PROBLEM!!!! (maybe)")
