from django.conf.urls.defaults import patterns, url
from django.conf import settings

urlpatterns = []

# only serve non-fqdn URLs
if ':' not in settings.STATICFILES_URL:
    urlpatterns += patterns('',
        url(r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve'),
    )
