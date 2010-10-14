import os
import urllib

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler, STATUS_CODE_TEXT
from django.http import Http404
from django.views import static

class StaticFilesHandler(WSGIHandler):
    """
    WSGI middleware that intercepts calls to the static files directory, as
    defined by the STATICFILES_URL setting, and serves those files.
    """
    media_dir = settings.STATICFILES_ROOT
    media_url = settings.STATICFILES_URL

    def __init__(self, application, media_dir=None):
        self.application = application
        if media_dir:
            self.media_dir = media_dir

    def file_path(self, url):
        """
        Returns the relative path to the media file on disk for the given URL.

        The passed URL is assumed to begin with ``media_url``.  If the
        resultant file path is outside the media directory, then a ValueError
        is raised.
        """
        # Remove ``media_url``.
        relative_url = url[len(self.media_url):]
        return urllib.url2pathname(relative_url)

    def serve(self, request, path):
        from django.contrib.staticfiles import finders
        absolute_path = finders.find(path)
        if not absolute_path:
            raise Http404('%r could not be matched to a static file.' % path)
        absolute_path, filename = os.path.split(absolute_path)
        return static.serve(request, path=filename, document_root=absolute_path)

    def __call__(self, environ, start_response):
        # Ignore requests that aren't under the media prefix.
        # Also ignore all requests if prefix isn't a relative URL.
        if (self.media_url.startswith('http://') or
            self.media_url.startswith('https://') or
                not environ['PATH_INFO'].startswith(self.media_url)):
            return self.application(environ, start_response)
        request = self.application.request_class(environ)
        try:
            response = self.serve(request, self.file_path(environ['PATH_INFO']))
        except Http404:
            status = '404 NOT FOUND'
            start_response(status, {'Content-type': 'text/plain'}.items())
            return [str('Page not found: %s' % environ['PATH_INFO'])]
        status_text = STATUS_CODE_TEXT[response.status_code]
        status = '%s %s' % (response.status_code, status_text)
        response_headers = [(str(k), str(v)) for k, v in response.items()]
        for c in response.cookies.values():
            response_headers.append(('Set-Cookie', str(c.output(header=''))))
        start_response(status, response_headers)
        return response

