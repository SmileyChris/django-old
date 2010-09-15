import os, posixpath

from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.utils.functional import LazyObject


class StaticFilesStorage(FileSystemStorage):
    """
    Standard file system storage for site media files.
    
    The defaults for ``location`` and ``base_url`` are
    ``STATICFILES_ROOT`` and ``STATICFILES_URL``.
    """
    staticfiles_location = (settings.STATICFILES_ROOT or
                            os.path.join(settings.MEDIA_ROOT, 'static'))
    staticfiles_base_url = (settings.STATICFILES_URL or
                            posixpath.join(settings.MEDIA_URL, 'static/'))

    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = self.staticfiles_location
        if base_url is None:
            base_url = self.staticfiles_base_url
        super(StaticFilesStorage, self).__init__(location, base_url, *args, **kwargs)


class DefaultStaticStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.STATICFILES_STORAGE)()

default_static_storage = DefaultStaticStorage()
