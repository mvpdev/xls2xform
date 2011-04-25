from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

from main import views as main_views

urlpatterns = patterns('',
    url(r"^$", main_views.index),
    url(r"^create_xform/", main_views.create_xform),
    url(r"^edit_xform/(?P<survey_id>\S+)/download/(?P<xform_file_name>\S*)", main_views.download_xform),
    url(r"^edit_xform/(?P<survey_id>\S+)/section/(?P<section_slug>\S+)/(?P<action>\S+)", main_views.edit_section),
    url(r"^edit_xform/(?P<survey_id>\S+)/validate", main_views.validate_xform),
    url(r"^edit_xform/(?P<survey_id>\S+)/debug_json", main_views.debug_json),
    url(r"^edit_xform/(?P<survey_id>\S+)/", main_views.edit_xform),
)


#(?P<pk>\d+)