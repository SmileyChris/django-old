import re
from django.conf.urls.defaults import patterns, url
from django.conf import settings

from django.contrib.staticfiles.views import serve

if '://' not in settings.STATICFILES_URL:
    base_url = re.escape(settings.STATICFILES_URL[1:])
    urlpatterns = patterns('',
        url(r'^%s(?P<path>.*)$' % base_url, serve, name='staticfiles-serve'),
    )
