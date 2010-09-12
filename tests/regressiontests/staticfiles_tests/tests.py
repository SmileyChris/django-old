from tempfile import mkdtemp
import shutil
import os
import sys
from cStringIO import StringIO
import posixpath
from django.test import TestCase, Client
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command

from django.contrib.staticfiles import resolvers

TEST_ROOT = os.path.dirname(__file__)

class FakeSettingsMixin:
    def fake_settings(self):
        self.old_staticfiles_url = settings.STATICFILES_URL
        self.old_staticfiles_root = settings.STATICFILES_ROOT
        self.old_staticfiles_dirs = settings.STATICFILES_DIRS

        self.old_media_root = settings.MEDIA_ROOT
        self.old_media_url = settings.MEDIA_URL

        settings.STATICFILES_URL = '/static/'
        settings.STATICFILES_ROOT = os.path.join(TEST_ROOT, 'project', 'site_media', 'static')

        settings.MEDIA_ROOT = os.path.join(TEST_ROOT, 'project', 'site_media', 'media')
        settings.MEDIA_URL = '/media/'

        settings.STATICFILES_DIRS = (os.path.join(TEST_ROOT, 'project', 'static'),)

    def restore_settings(self):
        settings.MEDIA_ROOT = self.old_media_root
        settings.MEDIA_URL = self.old_media_url

        settings.STATICFILES_ROOT = self.old_staticfiles_root
        settings.STATICFILES_URL = self.old_staticfiles_url

        settings.STATICFILES_DIRS = self.old_staticfiles_dirs

class UtilityAssertsTestCase(TestCase):
    """
    Test case with a couple utility assertions.

    """
    def _get_file(self, filepath):
        raise NotImplementedError

    def assertFileContains(self, filepath, text):
        self.failUnless(text in self._get_file(filepath),
                        "'%s' not in '%s'" % (text, filepath))

    def assertFileNotFound(self, filepath):
        self.assertRaises(IOError, self._get_file, filepath)

class BaseFileResolutionTests:
    """
    Tests shared by all file-resolving features (build_static,
    resolve_static, and static serve view).
    
    This relies on the asserts defined in UtilityAssertsTestCase, but
    is separated because some test cases need those asserts without
    all these tests.

    """
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

class TestResolveStatic(UtilityAssertsTestCase, BaseFileResolutionTests, FakeSettingsMixin):
    """
    Test ``resolve_static`` management command.

    """

    def setUp(self):
        self.fake_settings()

    def tearDown(self):
        self.restore_settings()

    def _get_file(self, filepath):
        _stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            call_command('resolve_static', filepath, all=False, verbosity='0')
            sys.stdout.seek(0)
            filepath = sys.stdout.read().strip()
            contents = open(filepath).read()
        finally:
            sys.stdout = _stdout
        return contents

    def test_all_files(self):
        """
        Test that resolve_static returns all candidate files if run
        without --first.

        """
        _stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            call_command('resolve_static', 'test/file.txt', verbosity='0')
            sys.stdout.seek(0)
            lines = [l.strip() for l in sys.stdout.readlines()]
        finally:
            sys.stdout = _stdout
        self.assertEquals(len(lines), 2)
        self.failUnless('project' in lines[0])
        self.failUnless('apps' in lines[1])

class BuildStaticTestCase(UtilityAssertsTestCase, FakeSettingsMixin):
    """
    Base setup for build_static tests.

    """
    def setUp(self):
        self.fake_settings()
        self._old_root = settings.STATICFILES_ROOT
        self.root = settings.STATICFILES_ROOT = mkdtemp()
        self.run_build_static()

    def tearDown(self):
        shutil.rmtree(self.root)
        settings.STATICFILES_ROOT = self._old_root
        self.restore_settings()

    def run_build_static(self, **kwargs):
        call_command('build_static', interactive=False, verbosity='0',
                     ignore_patterns=['*.ignoreme'], **kwargs)

    def _get_file(self, filepath):
        assert filepath, 'filepath is empty.'
        return open(os.path.join(self.root, filepath)).read()


class TestBuildStatic(BuildStaticTestCase, BaseFileResolutionTests, FakeSettingsMixin):
    """
    Test ``build_static`` management command.

    TODO: test alternate storages

    """
    def setUp(self):
        self.fake_settings()
        BuildStaticTestCase.setUp(self)

    def tearDown(self):
        BuildStaticTestCase.tearDown(self)
        self.restore_settings()

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


class TestBuildStaticExcludeNoDefaultIgnore(BuildStaticTestCase, FakeSettingsMixin):
    """
    Test ``--exclude-dirs`` and ``--no-default-ignore`` options for
    ``build_static`` management command.

    """
    def setUp(self):
        self.fake_settings()
        BuildStaticTestCase.setUp(self)

    def tearDown(self):
        BuildStaticTestCase.tearDown(self)
        self.restore_settings()

    def run_build_static(self):
        BuildStaticTestCase.run_build_static(self,
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

class TestBuildStaticDryRun(BuildStaticTestCase, FakeSettingsMixin):
    """
    Test ``--dry-run`` option for ``build_static`` management command.

    """
    def setUp(self):
        self.fake_settings()
        BuildStaticTestCase.setUp(self)

    def tearDown(self):
        BuildStaticTestCase.tearDown(self)
        self.restore_settings()

    def run_build_static(self):
        BuildStaticTestCase.run_build_static(self, dry_run=True)

    def test_no_files_created(self):
        """
        With --dry-run, no files created in destination dir.

        """
        self.assertEquals(os.listdir(self.root), [])
    

if sys.platform != 'win32':
    class TestBuildStaticLinks(BuildStaticTestCase, FakeSettingsMixin):
        """
        Test ``--link`` option for ``build_static`` management command.
        
        Note that by inheriting ``BaseFileResolutionTests`` we repeat all
        the standard file resolving tests here, to make sure using
        ``--link`` does not change the file-selection semantics.
        
        """
        def setUp(self):
            self.fake_settings()
            BuildStaticTestCase.setUp(self)

        def tearDown(self):
            BuildStaticTestCase.tearDown(self)
            self.restore_settings()

        def run_build_static(self):
            BuildStaticTestCase.run_build_static(self, link=True)

        def test_links_created(self):
            """
            With ``--link``, symbolic links are created.
            
            """
            self.failUnless(os.path.islink(os.path.join(self.root, 'test.txt')))

class TestServeStatic(UtilityAssertsTestCase, FakeSettingsMixin):
    """
    Test static asset serving view.

    """
    urls = "regressiontests.staticfiles_tests.urls"

    def setUp(self):
        self.fake_settings()
        self.client = Client()

    def tearDown(self):
        self.restore_settings()

    def _response(self, url):
        return self.client.get(posixpath.join(settings.STATICFILES_URL, url))

    def assertFileContains(self, filepath, text):
        self.assertContains(self._response(filepath), text)

    def assertFileNotFound(self, filepath):
        self.assertEquals(self._response(filepath).status_code, 404)

class TestServeMedia(TestCase, FakeSettingsMixin):
    """
    Test serving media from MEDIA_URL.

    """
    urls = "regressiontests.staticfiles_tests.urls"

    def setUp(self):
        self.fake_settings()
        self.client = Client()

    def tearDown(self):
        self.restore_settings()

    def test_serve_media(self):
        response = self.client.get(posixpath.join(settings.MEDIA_URL, 'media-file.txt'))
        self.assertContains(response, 'Media file.')

class TestServeAdminMedia(TestCase, FakeSettingsMixin):
    """
    Test serving media from django.contrib.admin.

    """
    urls = "regressiontests.staticfiles_tests.urls"

    def setUp(self):
        self.fake_settings()
        self.client = Client()

    def tearDown(self):
        self.restore_settings()

    def test_serve_admin_media(self):
        response = self.client.get(posixpath.join(settings.ADMIN_MEDIA_PREFIX, 'css/base.css'))
        self.assertContains(response, 'body')

class TestServeStaticBackwardCompat(TestServeStatic):
    urls = "regressiontests.staticfiles_tests.urls_backward_compat"

class TestServeMediaBackwardCompat(TestServeMedia):
    urls = "regressiontests.staticfiles_tests.urls_backward_compat"

class TestServeAdminMediaBackwardCompat(TestServeAdminMedia):
    urls = "regressiontests.staticfiles_tests.urls_backward_compat"

class ResolverTestCase:
    def test_resolve_first(self):
        src, dst = self.resolve_first
        self.assertEquals(self.resolver.resolve(src), dst)

    def test_resolve_all(self):
        src, dst = self.resolve_all
        self.assertEquals(self.resolver.resolve(src, all=True), dst)

class TestFileSystemFileResolver(UtilityAssertsTestCase, ResolverTestCase, FakeSettingsMixin):
    """
    Test FileSystemFileResolver.
    """
    def setUp(self):
        self.fake_settings()
        self.resolver = resolvers.FileSystemFileResolver()
        test_file_path = os.path.join(TEST_ROOT, 'project/static/test/file.txt')
        self.resolve_first = ("test/file.txt", test_file_path)
        self.resolve_all = ("test/file.txt", [test_file_path])

    def tearDown(self):
        self.restore_settings()

class TestAppDirectoriesFileResolver(UtilityAssertsTestCase, ResolverTestCase, FakeSettingsMixin):
    """
    Test AppDirectoriesFileResolver.
    """
    def setUp(self):
        self.fake_settings()
        self.resolver = resolvers.AppDirectoriesFileResolver()
        test_file_path = os.path.join(TEST_ROOT, 'apps/test/media/test/file1.txt')
        self.resolve_first = ("test/file1.txt", test_file_path)
        self.resolve_all = ("test/file1.txt", [test_file_path])

    def tearDown(self):
        self.restore_settings()

class TestDefaultStorageFileResolver(UtilityAssertsTestCase, ResolverTestCase, FakeSettingsMixin):
    """
    Test DefaultStorageFileResolver.
    """
    def setUp(self):
        self.fake_settings()
        self.resolver = resolvers.DefaultStorageFileResolver()
        test_file_path = os.path.join(TEST_ROOT, 'project/site_media/static/test/storage.txt')
        self.resolve_first = ("test/storage.txt", test_file_path)
        self.resolve_all = ("test/storage.txt", [test_file_path])

    def tearDown(self):
        self.restore_settings()

class TestMiscResolver(TestCase):
    """
    A few misc resolver tests.
    """
    def test_get_resolver(self):
        self.assertEquals(resolvers.FileSystemFileResolver,
            resolvers.get_resolver("django.contrib.staticfiles.resolvers.FileSystemFileResolver"))
        self.assertRaises(ImproperlyConfigured,
            resolvers.get_resolver, "django.contrib.staticfiles.resolvers.FooBarResolver")
        self.assertRaises(ImproperlyConfigured,
            resolvers.get_resolver, "foo.bar.FooBarResolver")
