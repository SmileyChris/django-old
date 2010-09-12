import unittest
from django.conf import settings, UserSettingsHolder, global_settings
from django.core.exceptions import ImproperlyConfigured

    
def setattr_settings(settings_module, attr, value):
    setattr(settings_module, attr, value)


class SettingsTests(unittest.TestCase):

    #
    # Regression tests for #10130: deleting settings.
    #

    def test_settings_delete(self):
        settings.TEST = 'test'
        self.assertEqual('test', settings.TEST)
        del settings.TEST
        self.assertRaises(AttributeError, getattr, settings, 'TEST')

    def test_settings_delete_wrapped(self):
        self.assertRaises(TypeError, delattr, settings, '_wrapped')


class MediaURLTests(unittest.TestCase):
    settings_module = settings

    def setUp(self):
        self._original_media_url = self.settings_module.MEDIA_URL

    def tearDown(self):
        self.settings_module.MEDIA_URL = self._original_media_url

    def test_blank(self):
        """
        If blank, no ImproperlyConfigured error will be raised, even though it
        doesn't end in a slash.
        """
        self.settings_module.MEDIA_URL = ''
        self.assertEqual('', self.settings_module.MEDIA_URL)

    def test_end_slash(self):
        """
        MEDIA_URL works if you end in a slash.
        """
        self.settings_module.MEDIA_URL = '/foo/'
        self.assertEqual('/foo/', self.settings_module.MEDIA_URL)

        self.settings_module.MEDIA_URL = 'http://media.foo.com/'
        self.assertEqual('http://media.foo.com/',
                         self.settings_module.MEDIA_URL)

    def test_no_end_slash(self):
        """
        MEDIA_URL raises an ImproperlyConfigured error if it doesn't end in a
        slash.
        """
        self.assertRaises(ImproperlyConfigured, setattr_settings,
                          self.settings_module, 'MEDIA_URL', '/foo')

        self.assertRaises(ImproperlyConfigured, setattr_settings,
                          self.settings_module, 'MEDIA_URL',
                          'http://media.foo.com')

    def test_double_slash(self):        
        """
        If a MEDIA_URL ends in more than one slash, presume they know what
        they're doing.
        """
        self.settings_module.MEDIA_URL = '/stupid//'
        self.assertEqual('/stupid//', self.settings_module.MEDIA_URL)

        self.settings_module.MEDIA_URL = 'http://media.foo.com/stupid//'
        self.assertEqual('http://media.foo.com/stupid//',
                         self.settings_module.MEDIA_URL)


class MediaURLUserSettingsHolderTests(unittest.TestCase):
    settings_module = UserSettingsHolder(global_settings)
