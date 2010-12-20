import fnmatch
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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


def check_settings():
    """
    Checks if the MEDIA_(ROOT|URL) and STATIC_(ROOT|URL)
    settings have the same value.
    """
    if settings.MEDIA_URL == settings.STATIC_URL:
        raise ImproperlyConfigured("The MEDIA_URL and STATIC_URL "
                                   "settings must have different values")
    if ((settings.MEDIA_ROOT and settings.STATIC_ROOT) and
            (settings.MEDIA_ROOT == settings.STATIC_ROOT)):
        raise ImproperlyConfigured("The MEDIA_ROOT and STATIC_ROOT "
                                   "settings must have different values")


def combine_listdir(all_dirs, all_files, partial_listdir):
    """
    Combines a 2-tuple containing a list of directories and a list files into
    master lists of directories and files. 
    """
    dirs, files = partial_listdir
    for dir in dirs:
        if dir not in all_dirs:
            all_dirs.append(dir)
    for file in files:
        if file not in all_files:
            all_files.append(file)


def storage_listdir(storage, path, prefix=None):
    if prefix:
        prefix += '/'
        if not path.startswith(prefix):
            return [], []
    else:
        prefix = ''
    path = path[len(prefix):]
    if not storage.exists(path):
        return [], []
    return storage.listdir(path)
