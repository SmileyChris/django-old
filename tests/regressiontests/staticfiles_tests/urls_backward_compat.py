from django.conf.urls.defaults import *

from django.contrib import admin

urlpatterns = patterns('',
    (r'', include('django.contrib.staticfiles.urls'))
)
