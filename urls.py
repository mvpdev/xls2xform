from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('xls2xform.xform_builder.urls')),
    url(r'original_xls2xform/', include('xls2xform.original_xls2xform.urls')),
    url(r'^accounts/', include('registration.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
