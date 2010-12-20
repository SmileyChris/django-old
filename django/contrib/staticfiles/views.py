"""
Views and functions for serving static files. These are only to be used during
development, and SHOULD NOT be used in a production setting.

"""
import mimetypes
import os
import posixpath
import re
import stat
import urllib
from email.Utils import parsedate_tz, mktime_tz

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotModified
from django.template import loader, Template, Context, TemplateDoesNotExist
from django.utils.http import http_date

from django.contrib.staticfiles import finders


def serve(request, path, document_root=None, show_indexes=False,
          insecure=False, index_prefix=None):
    """
    Serve static files below a given point in the directory structure or
    from locations inferred from the static files finders.

    To use, put a URL pattern such as::

        (r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve')

    in your URLconf.

    If you provide the ``document_root`` parameter, the file won't be looked
    up with the staticfiles finders, but in the given filesystem path, e.g.::

        (r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve',
         {'document_root' : '/path/to/my/files/'})

    You may also set ``show_indexes`` to ``True`` if you'd like to serve a
    basic index of the directory.  This index view will use the template
    hardcoded below, but if you'd like to override it, you can create a
    template called ``static/directory_index.html``. Use the ``index_prefix``
    argument to display the correct full path in indexes, for example::

        (r'^(?P<index_prefix>static/)(?P<path>.*)$',
         'django.contrib.staticfiles.views.serve', {'show_indexes': True}) 
    """
    print 't', path
    if not settings.DEBUG and not insecure:
        raise ImproperlyConfigured("The view to serve static files can only "
                                   "be used if the DEBUG setting is True or "
                                   "the --insecure option of 'runserver' is "
                                   "used")
    use_finders = not document_root
    # Clean up given path to only allow serving files below document_root.
    path = posixpath.normpath(urllib.unquote(path))
    path = path.lstrip('/')
    newpath = ''
    for part in path.split('/'):
        if not part:
            # Strip empty path components.
            continue
        drive, part = os.path.splitdrive(part)
        head, part = os.path.split(part)
        if part in (os.curdir, os.pardir):
            # Strip '.' and '..' in path.
            continue
        newpath = os.path.join(newpath, part).replace('\\', '/')
    if newpath and path != newpath:
        return HttpResponseRedirect(newpath)
    if use_finders:
        fullpath = finders.find(path)
    else:
        fullpath = os.path.join(document_root, newpath)
    if not fullpath:
        raise Http404('"%s" could not be found' % newpath)
    if os.path.isdir(fullpath):
        if show_indexes:
            if use_finders:
                fullpath = None
            return directory_index(newpath, fullpath, index_prefix)
        raise Http404("Directory indexes are not allowed here.")
    if not os.path.exists(fullpath):
        raise Http404('"%s" does not exist' % fullpath)
    # Respect the If-Modified-Since header.
    statobj = os.stat(fullpath)
    mimetype, encoding = mimetypes.guess_type(fullpath)
    mimetype = mimetype or 'application/octet-stream'
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj[stat.ST_MTIME], statobj[stat.ST_SIZE]):
        return HttpResponseNotModified(mimetype=mimetype)
    contents = open(fullpath, 'rb').read()
    response = HttpResponse(contents, mimetype=mimetype)
    response["Last-Modified"] = http_date(statobj[stat.ST_MTIME])
    response["Content-Length"] = len(contents)
    if encoding:
        response["Content-Encoding"] = encoding
    return response


DEFAULT_DIRECTORY_INDEX_TEMPLATE = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
    <meta http-equiv="Content-Language" content="en-us" />
    <meta name="robots" content="NONE,NOARCHIVE" />
    <title>Index of {{ directory }}</title>
  </head>
  <body>
    <h1>Index of {{ directory }}</h1>
    <ul>
      {% ifnotequal directory "/" %}
      <li><a href="../">../</a></li>
      {% endifnotequal %}
      {% for f in file_list %}
      <li><a href="{{ f|urlencode }}">{{ f }}</a></li>
      {% endfor %}
    </ul>
  </body>
</html>
"""

def directory_index(path, fullpath=None, prefix=None):
    try:
        t = loader.select_template(['static/directory_index.html',
                'static/directory_index'])
    except TemplateDoesNotExist:
        t = Template(DEFAULT_DIRECTORY_INDEX_TEMPLATE,
                     name='Default directory index template')
    if fullpath is None:
        dirs, files = finders.listdir(path)
    else:
        files = []
        dirs = []
        for f in os.listdir(fullpath):
            if os.path.isdir(os.path.join(fullpath, f)):
                dirs.append('%s/' % f)
            else:
                files.append(f)
    dirs = ['%s/' % f for f in dirs if not f.startswith('.')]
    files = [f for f in files if not f.startswith('.')]
    dirs.sort()
    files.sort()

    directory = '%s%s' % (prefix or '', path)
    if not directory.endswith('/'):
        directory = '%s/' % directory
    c = Context({
        'directory' : directory,
        'file_list' : dirs + files,
    })
    return HttpResponse(t.render(c))

def was_modified_since(header=None, mtime=0, size=0):
    """
    Was something modified since the user last downloaded it?

    header
      This is the value of the If-Modified-Since header.  If this is None,
      I'll just return True.

    mtime
      This is the modification time of the item we're talking about.

    size
      This is the size of the item we're talking about.
    """
    try:
        if header is None:
            raise ValueError
        matches = re.match(r"^([^;]+)(; length=([0-9]+))?$", header,
                           re.IGNORECASE)
        header_date = parsedate_tz(matches.group(1))
        if header_date is None:
            raise ValueError
        header_mtime = mktime_tz(header_date)
        header_len = matches.group(3)
        if header_len and int(header_len) != size:
            raise ValueError
        if mtime > header_mtime:
            raise ValueError
    except (AttributeError, ValueError, OverflowError):
        return True
    return False
