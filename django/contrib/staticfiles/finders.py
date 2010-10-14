import os
from django.conf import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from django.core.files.storage import default_storage
from django.utils.functional import memoize

from django.contrib.staticfiles import utils

_finders = {}


class BaseFinder(object):
    """
    A base file finder to be used for custom staticfiles finder classes.

    """
    def find(self, path, all=False):
        """
        Given a relative file path this ought to find an
        absolute file path.

        If the ``all`` parameter is ``False`` (default) only
        the first found file path will be returned; if set
        to ``True`` a list of all found files paths is returned.
        """
        raise NotImplementedError("Finder subclasses need to implement find()")


class FileSystemFinder(BaseFinder):
    """
    A static files finder that uses the ``STATICFILES_DIRS`` setting
    to locate files.
    """
    def find(self, path, all=False):
        """
        Looks for files in the extra media locations
        as defined in ``STATICFILES_DIRS``.
        """
        matches = []
        for root in settings.STATICFILES_DIRS:
            if isinstance(root, (list, tuple)):
                prefix, root = root
            else:
                prefix = ''
            matched_path = self.find_location(root, path, prefix)
            if matched_path:
                if not all:
                    return matched_path
                matches.append(matched_path)
        return matches

    def find_location(self, root, path, prefix=None):
        """
        Find a requested static file in a location, returning the found
        absolute path (or ``None`` if no match).
        """
        if prefix:
            prefix = '%s/' % prefix
            if not path.startswith(prefix):
                return None
            path = path[len(prefix):]
        path = os.path.join(root, path)
        if os.path.exists(path):
            return path


class AppDirectoriesFinder(BaseFinder):
    """
    A static files finder that looks in the ``media`` directory of each app.
    """
    def find(self, path, all=False):
        """
        Looks for files in the app directories.
        """
        matches = []
        for app in models.get_apps():
            app_matches = self.find_in_app(app, path, all=all)
            if app_matches:
                if not all:
                    return app_matches
                matches.extend(app_matches)
        return matches

    def find_in_app(self, app, path, all=False):
        """
        Find a requested static file in an app's media locations.

        If ``all`` is ``False`` (default), return the first matching
        absolute path (or ``None`` if no match). Otherwise return a list of
        found absolute paths.

        """
        prefix = utils.get_app_prefix(app)
        if prefix:
            prefix = '%s/' % prefix
            if not path.startswith(prefix):
                return []
            path = path[len(prefix):]
        paths = []
        storage = utils.app_static_storage(app)
        if storage and storage.exists(path):
            matched_path = storage.path(path)
            if not all:
                return matched_path
            paths.append(matched_path)
        return paths


class StorageFinder(BaseFinder):
    """
    A static files finder that uses the default storage backend.
    """
    static_storage = default_storage

    def __init__(self, storage=None, *args, **kwargs):
        if storage is not None:
            self.static_storage = storage
        super(StorageFinder, self).__init__(*args, **kwargs)

    def find(self, path, all=False):
        """
        Last resort, looks for files in the
        static files storage if it's local.
        """
        try:
            self.static_storage.path('')
        except NotImplementedError:
            pass
        else:
            if self.static_storage.exists(path):
                match = self.static_storage.path(path)
                if all:
                    match = [match]
                return match
        return []


def find(path, all=False):
    """
    Find a requested static file, first looking in any defined extra media
    locations and next in any (non-excluded) installed apps.
    
    If no matches are found and the static location is local, look for a match
    there too.
    
    If ``all`` is ``False`` (default), return the first matching
    absolute path (or ``None`` if no match). Otherwise return a list of
    found absolute paths.
    
    """
    matches = []
    for finder_path in settings.STATICFILES_FINDERS:
        finder = get_finder(finder_path)
        result = finder.find(path, all=all)
        if not all and result:
            return result
        if not isinstance(result, (list, tuple)):
            result = [result]
        matches.extend(result)

    if matches:
        return matches

    # No match.
    return all and [] or None


def _get_finder(import_path):
    """
    Imports the message storage class described by import_path, where
    import_path is the full Python path to the class.
    """
    module, attr = import_path.rsplit('.', 1)
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module, e))
    try:
        Finder = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '
                                   'class.' % (module, attr))
    if not issubclass(Finder, BaseFinder):
        raise ImproperlyConfigured('Finder "%s" is not a subclass of "%s"' %
                                   (Finder, BaseFinder))
    return Finder()
get_finder = memoize(_get_finder, _finders, 1)
