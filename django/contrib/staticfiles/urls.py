import re
from django.conf.urls.defaults import patterns, url
from django.conf import settings

urlpatterns = []

def staticfiles_urlpatterns():
    # use global urlpatterns to avoid multiple URL construction
    global urlpatterns
    if not urlpatterns:
        if ':' not in settings.STATICFILES_URL:
            base_url = re.escape(settings.STATICFILES_URL[1:])
            urlpatterns += patterns('django.contrib.staticfiles.views',
                url(r'^%s(?P<path>.*)$' % base_url, 'serve'),
            )
        if settings.MEDIA_ROOT and settings.MEDIA_URL and \
                                ':' not in settings.MEDIA_URL:
            base_url = re.escape(settings.MEDIA_URL[1:])
            urlpatterns += patterns('django.views.static',
                url(r'^%s(?P<path>.*)$' % base_url, 'serve',
                    {'document_root': settings.MEDIA_ROOT}),
            )
    return urlpatterns

# for backwards compatibility
urlpatterns = staticfiles_urlpatterns()
