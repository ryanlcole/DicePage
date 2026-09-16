"""Tests for distutils.command.bdist_rpm."""

import os
import shutil  # noqa: F401
import sys
from distutils.command.bdist_rpm import bdist_rpm
from distutils.core import Distribution
from distutils.tests import support

import pytest
from test.support import requires_zlib

SETUP_PY = """\
from distutils.core import setup
import foo

setup(name='foo', version='0.1', py_modules=['foo'],
      url='xxx', author='xxx', author_email='xxx')

"""


@pytest.fixture(autouse=True)
def sys_executable_encodable():
    try:
        sys.executable.encode('UTF-8')
    except UnicodeEncodeError:
        pytest.skip("sys.executable is not encodable to UTF-8")


mac_woes = pytest.mark.skipif(
    "not sys.platform.startswith('linux')",
    reason='spurious sdtout/stderr output under macOS',
)


@pytest.mark.usefixtures('save_env')
@pytest.mark.usefixtures('save_argv')
@pytest.mark.usefixtures('save_cwd')
class TestBuildRpm(
    support.TempdirManager,
):
    @mac_woes
    @requires_zlib()
    @pytest.mark.skipif("not shutil.which('rpm')")
    @pytest.mark.skipif("not shutil.which('rpmbuild')")
    def test_quiet(self):
        # 040855.python.test_bdist_rpm.line48.comment let's create a package
        tmp_dir = self.mkdtemp()
        os.environ['HOME'] = tmp_dir  # to confine dir '.rpmdb' creation
        pkg_dir = os.path.join(tmp_dir, 'foo')
        os.mkdir(pkg_dir)
        self.write_file((pkg_dir, 'setup.py'), SETUP_PY)
        self.write_file((pkg_dir, 'foo.py'), '#')
        self.write_file((pkg_dir, 'MANIFEST.in'), 'include foo.py')
        self.write_file((pkg_dir, 'README'), '')

        dist = Distribution({
            'name': 'foo',
            'version': '0.1',
            'py_modules': ['foo'],
            'url': 'xxx',
            'author': 'xxx',
            'author_email': 'xxx',
        })
        dist.script_name = 'setup.py'
        os.chdir(pkg_dir)

        sys.argv = ['setup.py']
        cmd = bdist_rpm(dist)
        cmd.fix_python = True

        # 040857.python.test_bdist_rpm.line73.comment running in quiet mode
        cmd.quiet = True
        cmd.ensure_finalized()
        cmd.run()

        dist_created = os.listdir(os.path.join(pkg_dir, 'dist'))
        assert 'foo-0.1-1.noarch.rpm' in dist_created

        # 040858.python.test_bdist_rpm.line81.comment bug #2945: upload ignores bdist_rpm files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.src.rpm') in dist.dist_files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.noarch.rpm') in dist.dist_files

    @mac_woes
    @requires_zlib()
    # 040859.python.test_bdist_rpm.line87.comment https://bugs.python.org/issue1533164
    @pytest.mark.skipif("not shutil.which('rpm')")
    @pytest.mark.skipif("not shutil.which('rpmbuild')")
    def test_no_optimize_flag(self):
        # 040860.python.test_bdist_rpm.line91.comment let's create a package that breaks bdist_rpm
        tmp_dir = self.mkdtemp()
        os.environ['HOME'] = tmp_dir  # to confine dir '.rpmdb' creation
        pkg_dir = os.path.join(tmp_dir, 'foo')
        os.mkdir(pkg_dir)
        self.write_file((pkg_dir, 'setup.py'), SETUP_PY)
        self.write_file((pkg_dir, 'foo.py'), '#')
        self.write_file((pkg_dir, 'MANIFEST.in'), 'include foo.py')
        self.write_file((pkg_dir, 'README'), '')

        dist = Distribution({
            'name': 'foo',
            'version': '0.1',
            'py_modules': ['foo'],
            'url': 'xxx',
            'author': 'xxx',
            'author_email': 'xxx',
        })
        dist.script_name = 'setup.py'
        os.chdir(pkg_dir)

        sys.argv = ['setup.py']
        cmd = bdist_rpm(dist)
        cmd.fix_python = True

        cmd.quiet = True
        cmd.ensure_finalized()
        cmd.run()

        dist_created = os.listdir(os.path.join(pkg_dir, 'dist'))
        assert 'foo-0.1-1.noarch.rpm' in dist_created

        # 040862.python.test_bdist_rpm.line123.comment bug #2945: upload ignores bdist_rpm files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.src.rpm') in dist.dist_files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.noarch.rpm') in dist.dist_files

        os.remove(os.path.join(pkg_dir, 'dist', 'foo-0.1-1.noarch.rpm'))
