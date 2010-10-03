import tempfile
import shutil
import os
import sys
from cStringIO import StringIO
import posixpath

from django.test import TestCase, Client
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db.models.loading import load_app

from django.contrib.staticfiles import finders, storage

TEST_ROOT = os.path.dirname(__file__)


class StaticFilesTestCase(TestCase):
    """
    Test case with a couple utility assertions.
    """
    def setUp(self):
        self.old_staticfiles_url = settings.STATICFILES_URL
        self.old_staticfiles_root = settings.STATICFILES_ROOT
        self.old_staticfiles_dirs = settings.STATICFILES_DIRS
        self.old_installed_apps = settings.INSTALLED_APPS
        self.old_media_root = settings.MEDIA_ROOT
        self.old_media_url = settings.MEDIA_URL
        self.old_admin_media_prefix = settings.ADMIN_MEDIA_PREFIX

        # We have to load these apps to test staticfiles.
        load_app('regressiontests.staticfiles_tests.apps.test')
        load_app('regressiontests.staticfiles_tests.apps.no_label')
        site_media = os.path.join(TEST_ROOT, 'project', 'site_media')
        settings.MEDIA_ROOT =  os.path.join(site_media, 'media')
        settings.MEDIA_URL = '/media/'
        settings.ADMIN_MEDIA_PREFIX = posixpath.join(settings.STATICFILES_URL, 'admin/')
        settings.STATICFILES_ROOT = os.path.join(site_media, 'static')
        settings.STATICFILES_URL = '/static/'
        settings.STATICFILES_DIRS = (
            os.path.join(TEST_ROOT, 'project', 'documents'),
        )

    def tearDown(self):
        settings.MEDIA_ROOT = self.old_media_root
        settings.MEDIA_URL = self.old_media_url
        settings.ADMIN_MEDIA_PREFIX = self.old_admin_media_prefix
        settings.STATICFILES_ROOT = self.old_staticfiles_root
        settings.STATICFILES_URL = self.old_staticfiles_url
        settings.STATICFILES_DIRS = self.old_staticfiles_dirs
        settings.INSTALLED_APPS = self.old_installed_apps

    def assertFileContains(self, filepath, text):
        self.failUnless(text in self._get_file(filepath),
                        "'%s' not in '%s'" % (text, filepath))

    def assertFileNotFound(self, filepath):
        self.assertRaises(IOError, self._get_file, filepath)


class TestingStaticFilesStorage(storage.StaticFilesStorage):

    def __init__(self, location=None, base_url=None, *args, **kwargs):
        location = tempfile.mkdtemp()
        settings.STATICFILES_ROOT = location
        super(TestingStaticFilesStorage, self).__init__(location, base_url, *args, **kwargs)


class BuildStaticTestCase(StaticFilesTestCase):
    """
    Tests shared by all file-resolving features (build_static,
    find_static, and static serve view).

    This relies on the asserts defined in UtilityAssertsTestCase, but
    is separated because some test cases need those asserts without
    all these tests.
    """
    def setUp(self):
        super(BuildStaticTestCase, self).setUp()
        self.old_staticfiles_storage = settings.STATICFILES_STORAGE
        self.old_root = settings.STATICFILES_ROOT
        settings.STATICFILES_STORAGE = 'regressiontests.staticfiles_tests.tests.TestingStaticFilesStorage'
        self.run_build_static()

    def tearDown(self):
        shutil.rmtree(settings.STATICFILES_ROOT)
        settings.STATICFILES_ROOT = self.old_root
        settings.STATICFILES_STORAGE = self.old_staticfiles_storage
        super(BuildStaticTestCase, self).tearDown()

    def run_build_static(self, **kwargs):
        call_command('build_static', interactive=False, verbosity='0',
                     ignore_patterns=['*.ignoreme'], **kwargs)

    def _get_file(self, filepath):
        assert filepath, 'filepath is empty.'
        filepath = os.path.join(settings.STATICFILES_ROOT, filepath)
        return open(filepath).read()


class TestDefaults:
    def test_staticfiles_dirs(self):
        """
        Can find a file in a STATICFILES_DIRS directory.

        """
        self.assertFileContains('test.txt', 'Can we find')

    def test_staticfiles_dirs_subdir(self):
        """
        Can find a file in a subdirectory of a STATICFILES_DIRS
        directory.

        """
        self.assertFileContains('subdir/test.txt', 'Can we find')

    def test_staticfiles_dirs_priority(self):
        """
        File in STATICFILES_DIRS has priority over file in app.

        """
        self.assertFileContains('test/file.txt', 'STATICFILES_DIRS')

    def test_app_files(self):
        """
        Can find a file in an app media/ directory.

        """
        self.assertFileContains('test/file1.txt', 'file1 in the app dir')


class TestBuildStatic(BuildStaticTestCase, TestDefaults):
    """
    Test ``build_static`` management command.
    """
    def test_ignore(self):
        """
        Test that -i patterns are ignored.
        """
        self.assertFileNotFound('test/test.ignoreme')

    def test_common_ignore_patterns(self):
        """
        Common ignore patterns (*~, .*, CVS) are ignored.
        """
        self.assertFileNotFound('test/.hidden')
        self.assertFileNotFound('test/backup~')
        self.assertFileNotFound('test/CVS')


class TestBuildStaticExcludeNoDefaultIgnore(BuildStaticTestCase):
    """
    Test ``--exclude-dirs`` and ``--no-default-ignore`` options for
    ``build_static`` management command.
    """
    def run_build_static(self):
        super(TestBuildStaticExcludeNoDefaultIgnore, self).run_build_static(
            exclude_dirs=True, use_default_ignore_patterns=False)

    def test_exclude_dirs(self):
        """
        With --exclude-dirs, cannot find file in
        STATICFILES_DIRS.

        """
        self.assertFileNotFound('test.txt')

    def test_no_common_ignore_patterns(self):
        """
        With --no-default-ignore, common ignore patterns (*~, .*, CVS)
        are not ignored.

        """
        self.assertFileContains('test/.hidden', 'should be ignored')
        self.assertFileContains('test/backup~', 'should be ignored')
        self.assertFileContains('test/CVS', 'should be ignored')


class TestBuildStaticDryRun(BuildStaticTestCase):
    """
    Test ``--dry-run`` option for ``build_static`` management command.
    """
    def run_build_static(self):
        super(TestBuildStaticDryRun, self).run_build_static(dry_run=True)

    def test_no_files_created(self):
        """
        With --dry-run, no files created in destination dir.
        """
        self.assertEquals(os.listdir(settings.STATICFILES_ROOT), [])


if sys.platform != 'win32':
    class TestBuildStaticLinks(BuildStaticTestCase, TestDefaults):
        """
        Test ``--link`` option for ``build_static`` management command.

        Note that by inheriting ``BaseFileResolutionTests`` we repeat all
        the standard file resolving tests here, to make sure using
        ``--link`` does not change the file-selection semantics.
        """
        def run_build_static(self):
            super(TestBuildStaticLinks, self).run_build_static(link=True)

        def test_links_created(self):
            """
            With ``--link``, symbolic links are created.

            """
            self.failUnless(os.path.islink(os.path.join(settings.STATICFILES_ROOT, 'test.txt')))


class TestServeStatic(StaticFilesTestCase):
    """
    Test static asset serving view.
    """
    urls = "regressiontests.staticfiles_tests.urls"

    def _response(self, filepath):
        return self.client.get(
            posixpath.join(settings.STATICFILES_URL, filepath))

    def assertFileContains(self, filepath, text):
        self.assertContains(self._response(filepath), text)

    def assertFileNotFound(self, filepath):
        self.assertEquals(self._response(filepath).status_code, 404)


class TestServeAdminMedia(TestServeStatic):
    """
    Test serving media from django.contrib.admin.
    """
    def test_serve_admin_media(self):
        media_file = posixpath.join(
            settings.ADMIN_MEDIA_PREFIX, 'css/base.css')
        response = self.client.get(media_file)
        self.assertContains(response, 'body')


class FinderTestCase:
    """
    Base finder test mixin
    """
    def test_find_first(self):
        src, dst = self.find_first
        self.assertEquals(self.finder.find(src), dst)

    def test_find_all(self):
        src, dst = self.find_all
        self.assertEquals(self.finder.find(src, all=True), dst)


class TestFileSystemFinder(StaticFilesTestCase, FinderTestCase):
    """
    Test FileSystemFinder.
    """
    def setUp(self):
        super(TestFileSystemFinder, self).setUp()
        self.finder = finders.FileSystemFinder()
        test_file_path = os.path.join(TEST_ROOT, 'project/documents/test/file.txt')
        self.find_first = ("test/file.txt", test_file_path)
        self.find_all = ("test/file.txt", [test_file_path])


class TestAppDirectoriesFinder(StaticFilesTestCase, FinderTestCase):
    """
    Test AppDirectoriesFinder.
    """
    def setUp(self):
        super(TestAppDirectoriesFinder, self).setUp()
        self.finder = finders.AppDirectoriesFinder()
        test_file_path = os.path.join(TEST_ROOT, 'apps/test/media/test/file1.txt')
        self.find_first = ("test/file1.txt", test_file_path)
        self.find_all = ("test/file1.txt", [test_file_path])


class TestStorageFinder(StaticFilesTestCase, FinderTestCase):
    """
    Test StorageFinder.
    """
    def setUp(self):
        super(TestStorageFinder, self).setUp()
        self.finder = finders.StorageFinder(
            storage=storage.StaticFilesStorage(location=settings.MEDIA_ROOT))
        test_file_path = os.path.join(settings.MEDIA_ROOT, 'media-file.txt')
        self.find_first = ("media-file.txt", test_file_path)
        self.find_all = ("media-file.txt", [test_file_path])


class TestMiscFinder(TestCase):
    """
    A few misc finder tests.
    """
    def test_get_finder(self):
        self.assertEquals(finders.FileSystemFinder,
            finders.get_finder("django.contrib.staticfiles.finders.FileSystemFinder"))
        self.assertRaises(ImproperlyConfigured,
            finders.get_finder, "django.contrib.staticfiles.finders.FooBarFinder")
        self.assertRaises(ImproperlyConfigured,
            finders.get_finder, "foo.bar.FooBarFinder")

