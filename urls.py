#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from django.conf import settings

from views import convert_file
from views import download_xform

# want to use this directory (pwd) rather than media_root

urlpatterns = patterns('',
                       (r'^$', convert_file),
                       (r'^example_xls/(?P<path>.*)$', 'django.views.static.serve',
			{'document_root': settings.MEDIA_ROOT + 'xls2xform/example_xls'}),
                       (r'^(?P<path>submissions/.*)$', download_xform)
                       )
