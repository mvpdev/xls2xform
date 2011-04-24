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
            #check to see if the new section is a duplicate
            #assuming not--
            remove_section = slug_dict[slug]
        else:
            remove_section = None
        
        nv = lv._clone()
        nv.sections.remove(remove_section)
        #check to see if the new section is a duplicate
        
        new_section.save()
        nv.sections.add(new_section)
        
        self.latest_version = nv
        self.save()
        return nv
    
    def order_base_sections(self, slug_list):
        v = self.latest_version._clone()
        new_base = v.base_section
        slug_list_includes = []
        for slug in slug_list:
            slug_list_includes.append({u'include': slug})
        new_base.section_json = json.dumps(slug_list_includes)
        new_base.save()
        v.save()
        
        self.latest_version = v
        self.save()

class XFormVersion(models.Model):
    xform = models.ForeignKey(XForm, related_name="versions")
    date_created = models.DateTimeField(auto_now_add=True)
    base_section = models.ForeignKey('XFormSection', null=True)
        
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
        for s in self.sections.all():
            sections[s.slug] = s
        return sections

class XFormSection(models.Model):
    slug = models.CharField(max_length=32)
    section_json = models.TextField()
    versions = models.ManyToManyField("XFormVersion", related_name="sections")
    
    def __init__(self, *args, **kwargs):
        """
        converts a section_dict argument to json.
        """
        d = kwargs.pop(u'section_dict', kwargs.pop('section_dict', None))
        if d is not None: kwargs[u'section_json'] = json.dumps(d)
        return super(XFormSection, self).__init__(*args, **kwargs)
    
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
