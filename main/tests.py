"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from main.models import *

class XFormCreationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.xform = XForm.objects.create(user=self.user, id_string="SimpleId")
    
    def test_version(self):
        #one version exists by default
        self.assertEqual(self.xform.versions.count(), 1)
        #version is empty
        self.assertEqual(self.xform.latest_version.sections.count(), 0)
    
    def test_add_section(self):
        sd1 = {u'type':u'text', u'name': u'colour'}
        first_version = self.xform.add_or_update_section(section_dict=sd1, slug="first_section")
        
        #VERSION COUNT INCREMENTED
        self.assertEqual(self.xform.versions.count(), 2)
        
        #the latest_version should have one section
        self.assertEqual(self.xform.latest_version.sections.count(), 1)
        
        #  -- add_or_update_section updates when the slug matches
        sd2 = {u'type':u'text', u'name': u'color'}
        second_version = self.xform.add_or_update_section(section_dict=sd2, slug="first_section")
        
        #  -- the first version should not equal the second version, and other similar tests
        self.assertTrue(first_version != second_version)
        
        #VERSION COUNT INCREMENTED
        self.assertEqual(self.xform.versions.count(), 3)
        
        #the latest version should have 1 section still
        self.assertEqual(self.xform.latest_version.sections.count(), 1)
    
    def tearDown(self):
        self.user.delete()
        self.xform.delete()

class SectionOrderingViaBaseSection(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.xform = XForm.objects.create(user=self.user, id_string="SimpleId")
    
    def test_empty_form_has_empty_base_section(self):
        version = self.xform.latest_version
        self.assertEqual([], version.base_section._questions_list())
    
    def test_new_section_is_not_yet_added(self):
        """
        Adding a section to an xform shouldn't add it to the base section.
        That is done in the UI.
        """
        sd1 = [{u'type':u'text', u'name':u'color'}]
        self.xform.add_or_update_section(section_dict=sd1, slug="first_section")
        
        sd2 = [{u'type':u'text', u'name':u'feeling'}]
        self.xform.add_or_update_section(section_dict=sd2, slug="second_section")
        
        version = self.xform.latest_version
        self.assertEqual([], version.base_section._questions_list())
        self.assertEqual(3, self.xform.versions.count())
        
        # only when the user chooses to place the sections, 
        # they should be added to the base_section.
        self.xform.order_base_sections(["first_section", "second_section"])
        self.assertEqual(4, self.xform.versions.count())
        
        included_slugs = self.xform.latest_version.base_section._questions_list()
        self.assertEqual(included_slugs, [{u'include':u'first_section'}, {u'include':u'second_section'}])

class ExportingFormViaPyxform(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.xform = XForm.objects.create(user=self.user, id_string="SimpleId")
    
    def test_export(self):
        self.assertEqual(self.xform.versions.count(), 1)
        
        #set section_json
        sd = [{u'type':u'text', u'name':u'color'}]
        lv = self.xform.add_or_update_section(section_dict=sd, slug="first_section")
        
        s = self.xform.export_survey()
        survey_id = s.id_string()
        
        self.assertEqual(s.to_xml(), """<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><h:head><h:title>SimpleId</h:title><model><instance><SimpleId id="%s"><color/></SimpleId></instance><bind nodeset="/SimpleId/color" required="true()" type="string"/></model></h:head><h:body><input ref="/SimpleId/color"><label ref="jr:itext('/SimpleId/color:label')"/></input></h:body></h:html>""" % survey_id)
        
        sd2 = [{u'type': u'integer', u'name': u'weight'}]
        lv2 = self.xform.add_or_update_section(section_dict=sd2, slug="second_section")
        
        s = self.xform.export_survey()
        self.assertEqual("""<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><h:head><h:title>SimpleId</h:title><model><instance><SimpleId id="%s"><color/><weight/></SimpleId></instance><bind nodeset="/SimpleId/color" required="true()" type="string"/><bind nodeset="/SimpleId/weight" required="true()" type="int"/></model></h:head><h:body><input ref="/SimpleId/color"><label ref="jr:itext('/SimpleId/color:label')"/></input><input ref="/SimpleId/weight"><label ref="jr:itext('/SimpleId/weight:label')"/></input></h:body></h:html>"""  % survey_id, s.to_xml())
    
    def tearDown(self):
        self.user.delete()
        self.xform.delete()
