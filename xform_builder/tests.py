"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client

from xform_builder.models import *

from django.contrib.auth.models import User

class TestIndexView(TestCase):
    def setUp(self):
        admin = User.objects.create(username="admin")
        admin.set_password("pass")
        admin.save()
        self.c = Client()
        #log in
        self.c.login(username="admin", password="pass")

    def post_new_form(self, id_string, title):
        response = self.c.post("/", {
            'id_string': id_string,
            'title': title,
        }, follow=True)
        self.assertTrue(len(response.redirect_chain) > 0)
        def spaces_subbed(str):
            import re
            return re.sub(" ", "_", str)
        self.assertEquals(response.redirect_chain[0][0], "http://testserver/edit/%s" % spaces_subbed(id_string))

    def test_new_forms(self):
        inputs = [
            ('id_string1', 'title1'),
            ('id string2', 'title2'), # definitely wont pass
            ('id_string3', 'title with space'),
            #('', 'title'), # definitely wont pass
            #('id_string', ''), # definitely wont pass
            ]
        for input in inputs:
            # XForm.objects.create({
            #     'id_string': input[0],
            #     'title': input[1]
            # })
            self.post_new_form(*input)

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

        #we should be able to remove that section
        self.xform.remove_section(slug="first_section")
        self.assertEqual(self.xform.latest_version.sections.count(), 0)
        #removing a section creates a new version
        self.assertEqual(self.xform.versions.count(), 4)

    def tearDown(self):
        self.user.delete()
        self.xform.delete()


class SectionOrderingViaBaseSection(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.xform = XForm.objects.create(user=self.user, id_string="SimpleId")

        sd1 = [{u'type':u'text', u'name':u'color'}]
        self.xform.add_or_update_section(section_dict=sd1, slug="first_section")

        sd2 = [{u'type':u'text', u'name':u'feeling'}]
        self.xform.add_or_update_section(section_dict=sd2, slug="second_section")

    def test_empty_form_has_empty_base_section(self):
        version = self.xform.latest_version
        self.assertEqual([], version.base_section.questions_list)

    def test_new_section_is_not_yet_added(self):
        """
        Adding a section to an xform shouldn't add it to the base section.
        """
        version = self.xform.latest_version
        self.assertEqual([], version.base_section.questions_list)
        self.assertEqual(3, self.xform.versions.count())
        
        # only when the user chooses to place the sections, 
        # they should be added to the base_section.
        self.xform.order_base_sections(["first_section", "second_section"])
        self.assertEqual(4, self.xform.versions.count())
        
        included_slugs = self.xform.latest_version.base_section.questions_list
        expected_dict = [{u'type':u'include', 'name':u'first_section'}, {u'type':u'include', u'name': u'second_section'}]
        self.assertEqual(included_slugs, expected_dict)
    
    def test_activation_of_section(self):
        section_portfolio, included_base_sections = self.xform.latest_version.all_sections()
        #by default, no sections are included
        self.assertEqual(len(included_base_sections), 0)
        version_count = self.xform.versions.count()
        
        #'activating' one section adds it to the base sections.
        self.xform.activate_section(section_portfolio[0])
        included_base_sections2 = self.xform.latest_version.included_base_sections()
        self.assertEqual(len(included_base_sections2), 1)
        self.assertEqual(self.xform.versions.count(), version_count+1)
        
        #'deactivating' will return the list to the original length.
        self.xform.deactivate_section(section_portfolio[0])
        included_base_sections3 = self.xform.latest_version.included_base_sections()
        self.assertEqual(len(included_base_sections3), 0)
        self.assertEqual(self.xform.versions.count(), version_count+2)
    
    def test_sub_sections_are_recognized(self):
        #a bottom-level include (simple case)
        sd3 = [{u'type':u'include', u'name':u'location'}]
        nv = self.xform.add_or_update_section(section_dict=sd3, slug="some_include")
        incl = nv.sections.get(slug="some_include")
        self.assertEqual(incl.sub_sections(), ['location'])
        
        #a section with an include in a repeat (slightly more complex)
        sd4 = [{u'type':u'loop', u'children':[{u'type': u'include', u'name': u'include2'}]}]
        nv = self.xform.add_or_update_section(section_dict=sd4, slug="some_include2")
        incl = nv.sections.get(slug="some_include2")
        self.assertEqual(incl.sub_sections(), ['include2'])
        #todo: deeper levels of include-ability?


class ExportingFormViaPyxform(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.xform = XForm.objects.create(user=self.user,
                                          id_string=u"SimpleId",
                                          title=u"SimpleId")

    def test_export(self):
        self.assertEqual(self.xform.versions.count(), 1)

        #set section_json
        kwargs = {
            u'section_dict': {
                u'type': u'survey',
                u'name': u'first_section',
                u'children': [
                    {
                        u'type': u'text',
                        u'name': u'color'
                        }
                    ],
                },
            u'slug': u'first_section',
            }
        lv = self.xform.add_or_update_section(**kwargs)
        self.assertEqual(lv, self.xform.latest_version)

        # note: I needed to activate the section to get things working
        new_section = lv.sections_by_slug()[u'first_section']
        lv = self.xform.activate_section(new_section)
        #self.xform.order_sections([u'first_section'])
        s = self.xform.export_survey()
        pyxform_survey_id = s.id_string

        # The latest version generates a unique id and passes it in
        # the survey object. pyxform should use it.
        self.assertEqual(lv.get_unique_id(), pyxform_survey_id)
        self.maxDiff = 3000
        self.assertEqual(s.to_xml().strip(), """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>SimpleId</h:title>
    <model>
      <instance>
        <SimpleId id="%s">
          <color/>
        </SimpleId>
      </instance>
      <bind nodeset="/SimpleId/color" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/SimpleId/color"/>
  </h:body>
</h:html>
            """.strip() % pyxform_survey_id)
        
        sd2 = [
            {
                u'type': u'integer',
                u'name': u'weight'
                }
            ]
        lv2 = self.xform.add_or_update_section(section_dict=sd2, slug="second_section")
        second_section = lv2.sections_by_slug()['second_section']
        lv2 = self.xform.activate_section(second_section)
        pyxform_survey_id = lv2.get_unique_id()

        s = self.xform.export_survey()
        expected = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>SimpleId</h:title>
    <model>
      <instance>
        <SimpleId id="%s">
          <color/>
          <weight/>
        </SimpleId>
      </instance>
      <bind nodeset="/SimpleId/color" type="string"/>
      <bind nodeset="/SimpleId/weight" type="int"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/SimpleId/color"/>
    <input ref="/SimpleId/weight"/>
  </h:body>
</h:html>
        """ % pyxform_survey_id
        output = s.to_xml()
        self.assertEqual(output.strip(), expected.strip())

    def tearDown(self):
        self.user.delete()
        self.xform.delete()

import pyxform

class PassValuesToPyxform(TestCase):
    def setUp(self):
        main_section = {
            "type": "survey",
            "name": "MyName",
            "children": [{
                    u'type': u'text',
                    u'name': u'name'
                   }]
        }
        self.title = "TestAsurvey"
        self.id_string = "Test_canSpecifyIDstring"
        self.s = pyxform.create_survey(title=self.title, main_section=main_section, \
                        id_string=self.id_string)

    def test_package_values_create_survey(self):
        self.assertEqual(self.s.title, self.title)
        self.assertEqual(self.s.id_string, self.id_string)
        self.assertEqual(len(self.s.children), 1)

    def test_odk_validate(self):
        # TODO: write a test for a form that should validate
        #       and a form that should not validate.
        self.s.to_xml()
