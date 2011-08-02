from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

from xform_builder import views as main_views

urlpatterns = patterns('',
    url(r"^quick_converter/$", main_views.quick_converter),
    url(r"^$", main_views.index),
    url(r"^edit/(?P<survey_id>\S+)/download/$", main_views.download_xform),
    url(r"^edit/(?P<survey_id>\S+)/download/(?P<version_number>\S+)/(?P<xform_file_name>\S+)\.xml", main_views.download_xform),
    url(r"^edit/(?P<survey_id>\S+)/section/(?P<section_slug>\S+)/(?P<action>\S+)", main_views.edit_section),
#    url(r"^edit/(?P<survey_id>\S+)/validate", main_views.validate_xform),
    url(r"^edit/(?P<survey_id>\S+)/debug_json", main_views.debug_json),
    url(r"^edit/(?P<survey_id>\S+)/", main_views.edit_xform),
)


#(?P<pk>\d+)
