from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

from main import views as main_views

urlpatterns = patterns('',
    url(r"^$", main_views.index),
)
