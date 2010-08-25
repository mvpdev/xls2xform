from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from django.conf import settings

from views import convert_file
from views import download_xform

urlpatterns = patterns('',
		(r'^$', convert_file),
		(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
			{'document_root': '%sxls2xform/webcontent' % settings.MEDIA_ROOT}),
		(r'^example_xls/(?P<path>.*)$', 'django.views.static.serve',
			{'document_root': '%sxls2xform/example_xls' % settings.MEDIA_ROOT}),
		(r'^(?P<path>submissions/.*)$', download_xform)
)
