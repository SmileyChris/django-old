import os
import fnmatch

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.importlib import import_module

def get_files_for_app(app, ignore_patterns=[]):
    """
    Return a list containing the relative source paths for all files that
    should be copied for an app.
    
    """
    prefix = get_app_prefix(app)
    files = []
    storage = app_static_storage(app)
    if storage:
        for path in get_files(storage, ignore_patterns):
            if prefix:
                path = '/'.join([prefix, path])
            files.append(path)
    return files

def app_static_storage(app):
    """
    Returns a static file storage if available in the given app.
    
    """
    # "app" is actually the models module of the app. Remove the '.models'. 
    app_module = '.'.join(app.__name__.split('.')[:-1])

    # The models module may be a package in which case dirname(app.__file__)
    # would be wrong. Import the actual app as opposed to the models module.
    app = import_module(app_module)
    app_root = os.path.dirname(app.__file__)
    location = os.path.join(app_root, 'media')
    if not os.path.isdir(location):
        return None

    return FileSystemStorage(location=location)

def get_app_prefix(app):
    """
    Return the path name that should be prepended to files for this app.
    
    """
    # "app" is actually the models module of the app. Remove the '.models'. 
    bits = app.__name__.split('.')[:-1]
    app_name = bits[-1]
    app_module = '.'.join(bits)
    if app_module == 'django.contrib.admin':
        return app_name
    else:
        return None

def get_files(storage, ignore_patterns=[], location=''):
    """
    Recursively walk the storage directories gathering a complete list of files
    that should be copied, returning this list.
    
    """

    def is_ignored(path):
        """
        Return True or False depending on whether the ``path`` should be
        ignored (if it matches any pattern in ``ignore_patterns``).
        
        """
        for pattern in ignore_patterns:
            if fnmatch.fnmatchcase(path, pattern):
                return True
        return False

    directories, files = storage.listdir(location)
    static_files = [location and '/'.join([location, fn]) or fn
                    for fn in files
                    if not is_ignored(fn)]
    for dir in directories:
        if is_ignored(dir):
            continue
        if location:
            dir = '/'.join([location, dir])
        static_files.extend(get_files(storage, ignore_patterns, dir))
    return static_files
