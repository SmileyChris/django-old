import os, posixpath

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.utils.functional import LazyObject


class StaticFilesStorage(FileSystemStorage):
    """
    Standard file system storage for site media files.
    
    The defaults for ``location`` and ``base_url`` are
    ``STATICFILES_ROOT`` and ``STATICFILES_URL``.
    """
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = settings.STATICFILES_ROOT
        if base_url is None:
            base_url = settings.STATICFILES_URL
        if not location:
            raise ImproperlyConfigured("You're using the staticfiles app "
                "without having set the STATICFILES_ROOT setting. Set it to "
                "the absolute path of the directory that holds static media.")
        if not base_url:
            raise ImproperlyConfigured("You're using the staticfiles app "
                "without having set the STATICFILES_URL setting. Set it to "
                "URL that handles the files served from STATICFILES_ROOT.")
        super(StaticFilesStorage, self).__init__(location, base_url, *args, **kwargs)
