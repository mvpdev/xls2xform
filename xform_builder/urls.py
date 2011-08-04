from django.conf.urls.defaults import patterns, url

from xform_builder import views as main_views

# todo: improve the regular expression \S+
EDIT_XFORM = r"^edit/(?P<survey_id>.+)/"

urlpatterns = patterns('',
    url(r"^$", main_views.home),
    url(EDIT_XFORM + r"section/(?P<section_slug>\S+)/(?P<action>\S+)", main_views.edit_section),
    url(EDIT_XFORM + r"debug_json", main_views.debug_json),
    url(EDIT_XFORM + r"", main_views.edit_xform),
    url("^download/(?P<survey_id>.+)\.(?P<format>json|xml)", main_views.download_xform)
)
