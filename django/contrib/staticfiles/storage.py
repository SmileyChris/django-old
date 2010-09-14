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
        super(StaticFilesStorage, self).__init__(location, base_url, *args, **kwargs)


class DefaultStaticStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.STATICFILES_STORAGE)()


default_static_storage = DefaultStaticStorage()
