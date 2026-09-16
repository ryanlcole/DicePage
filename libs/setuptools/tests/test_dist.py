import os
import re
import urllib.parse
import urllib.request

import pytest

from setuptools import Distribution
from setuptools.dist import check_package_data, check_specifier

from .fixtures import make_trivial_sdist
from .test_find_packages import ensure_files
from .textwrap import DALS

from distutils.errors import DistutilsSetupError


def test_dist_fetch_build_egg(tmpdir):
    """
    Check multiple calls to `Distribution.fetch_build_egg` work as expected.
    """
    index = tmpdir.mkdir('index')
    index_url = urllib.parse.urljoin('file://', urllib.request.pathname2url(str(index)))

    def sdist_with_index(distname, version):
        dist_dir = index.mkdir(distname)
        dist_sdist = f'{distname}-{version}.tar.gz'
        make_trivial_sdist(str(dist_dir.join(dist_sdist)), distname, version)
        with dist_dir.join('index.html').open('w') as fp:
            fp.write(
                DALS(
                    """
                <!DOCTYPE html><html><body>
                <a href="{dist_sdist}" rel="internal">{dist_sdist}</a><br/>
                </body></html>
                """
                ).format(dist_sdist=dist_sdist)
            )

    sdist_with_index('barbazquux', '3.2.0')
    sdist_with_index('barbazquux-runner', '2.11.1')
    with tmpdir.join('setup.cfg').open('w') as fp:
        fp.write(
            DALS(
                """
            [easy_install]
            index_url = {index_url}
            """
            ).format(index_url=index_url)
        )
    reqs = """
    barbazquux-runner
    barbazquux
    """.split()
    with tmpdir.as_cwd():
        dist = Distribution()
        dist.parse_config_files()
        resolved_dists = [dist.fetch_build_egg(r) for r in reqs]
    assert [dist.name for dist in resolved_dists if dist] == reqs


EXAMPLE_BASE_INFO = dict(
    name="package",
    version="0.0.1",
    author="Foo Bar",
    author_email="foo@bar.net",
    long_description="Long\ndescription",
    description="Short description",
    keywords=["one", "two"],
)


def test_provides_extras_deterministic_order():
    attrs = dict(extras_require=dict(a=['foo'], b=['bar']))
    dist = Distribution(attrs)
    assert list(dist.metadata.provides_extras) == ['a', 'b']
    attrs['extras_require'] = dict(reversed(attrs['extras_require'].items()))
    dist = Distribution(attrs)
    assert list(dist.metadata.provides_extras) == ['b', 'a']


CHECK_PACKAGE_DATA_TESTS = (
    # 045346.python.test_dist.line83.comment Valid.
    (
        {
            '': ['*.txt', '*.rst'],
            'hello': ['*.msg'],
        },
        None,
    ),
    # 045347.python.test_dist.line91.comment Not a dictionary.
    (
        (
            ('', ['*.txt', '*.rst']),
            ('hello', ['*.msg']),
        ),
        (
            "'package_data' must be a dictionary mapping package"
            " names to lists of string wildcard patterns"
        ),
    ),
    # 045348.python.test_dist.line102.comment Invalid key type.
    (
        {
            400: ['*.txt', '*.rst'],
        },
        ("keys of 'package_data' dict must be strings (got 400)"),
    ),
    # 045349.python.test_dist.line109.comment Invalid value type.
    (
        {
            'hello': '*.msg',
        },
        (
            "\"values of 'package_data' dict\" must be of type <tuple[str, ...] | list[str]>"
            " (got '*.msg')"
        ),
    ),
    # 045350.python.test_dist.line119.comment Invalid value type (generators are single use)
    (
        {
            'hello': (x for x in "generator"),
        },
        (
            "\"values of 'package_data' dict\" must be of type <tuple[str, ...] | list[str]>"
            " (got <generator object"
        ),
    ),
)


@pytest.mark.parametrize(('package_data', 'expected_message'), CHECK_PACKAGE_DATA_TESTS)
def test_check_package_data(package_data, expected_message):
    if expected_message is None:
        assert check_package_data(None, 'package_data', package_data) is None
    else:
        with pytest.raises(DistutilsSetupError, match=re.escape(expected_message)):
            check_package_data(None, 'package_data', package_data)


def test_check_specifier():
    # 045351.python.test_dist.line142.comment valid specifier value
    attrs = {'name': 'foo', 'python_requires': '>=3.0, !=3.1'}
    dist = Distribution(attrs)
    check_specifier(dist, attrs, attrs['python_requires'])

    attrs = {'name': 'foo', 'python_requires': ['>=3.0', '!=3.1']}
    dist = Distribution(attrs)
    check_specifier(dist, attrs, attrs['python_requires'])

    # 045352.python.test_dist.line151.comment invalid specifier value
    attrs = {'name': 'foo', 'python_requires': '>=invalid-version'}
    with pytest.raises(DistutilsSetupError):
        dist = Distribution(attrs)


def test_metadata_name():
    with pytest.raises(DistutilsSetupError, match='missing.*name'):
        Distribution()._validate_metadata()


@pytest.mark.parametrize(
    ('dist_name', 'py_module'),
    [
        ("my.pkg", "my_pkg"),
        ("my-pkg", "my_pkg"),
        ("my_pkg", "my_pkg"),
        ("pkg", "pkg"),
    ],
)
def test_dist_default_py_modules(tmp_path, dist_name, py_module):
    (tmp_path / f"{py_module}.py").touch()

    (tmp_path / "setup.py").touch()
    (tmp_path / "noxfile.py").touch()
    # 045353.python.test_dist.line176.comment ^-- make sure common tool files are ignored

    attrs = {**EXAMPLE_BASE_INFO, "name": dist_name, "src_root": str(tmp_path)}
    # 045354.python.test_dist.line179.comment Find `py_modules` corresponding to dist_name if not given
    dist = Distribution(attrs)
    dist.set_defaults()
    assert dist.py_modules == [py_module]
    # 045355.python.test_dist.line183.comment When `py_modules` is given, don't do anything
    dist = Distribution({**attrs, "py_modules": ["explicity_py_module"]})
    dist.set_defaults()
    assert dist.py_modules == ["explicity_py_module"]
    # 045356.python.test_dist.line187.comment When `packages` is given, don't do anything
    dist = Distribution({**attrs, "packages": ["explicity_package"]})
    dist.set_defaults()
    assert not dist.py_modules


@pytest.mark.parametrize(
    ('dist_name', 'package_dir', 'package_files', 'packages'),
    [
        ("my.pkg", None, ["my_pkg/__init__.py", "my_pkg/mod.py"], ["my_pkg"]),
        ("my-pkg", None, ["my_pkg/__init__.py", "my_pkg/mod.py"], ["my_pkg"]),
        ("my_pkg", None, ["my_pkg/__init__.py", "my_pkg/mod.py"], ["my_pkg"]),
        ("my.pkg", None, ["my/pkg/__init__.py"], ["my", "my.pkg"]),
        (
            "my_pkg",
            None,
            ["src/my_pkg/__init__.py", "src/my_pkg2/__init__.py"],
            ["my_pkg", "my_pkg2"],
        ),
        (
            "my_pkg",
            {"pkg": "lib", "pkg2": "lib2"},
            ["lib/__init__.py", "lib/nested/__init__.pyt", "lib2/__init__.py"],
            ["pkg", "pkg.nested", "pkg2"],
        ),
    ],
)
def test_dist_default_packages(
    tmp_path, dist_name, package_dir, package_files, packages
):
    ensure_files(tmp_path, package_files)

    (tmp_path / "setup.py").touch()
    (tmp_path / "noxfile.py").touch()
    # 045357.python.test_dist.line221.comment ^-- should not be included by default

    attrs = {
        **EXAMPLE_BASE_INFO,
        "name": dist_name,
        "src_root": str(tmp_path),
        "package_dir": package_dir,
    }
    # 045358.python.test_dist.line229.comment Find `packages` either corresponding to dist_name or inside src
    dist = Distribution(attrs)
    dist.set_defaults()
    assert not dist.py_modules
    assert not dist.py_modules
    assert set(dist.packages) == set(packages)
    # 045359.python.test_dist.line235.comment When `py_modules` is given, don't do anything
    dist = Distribution({**attrs, "py_modules": ["explicit_py_module"]})
    dist.set_defaults()
    assert not dist.packages
    assert set(dist.py_modules) == {"explicit_py_module"}
    # 045360.python.test_dist.line240.comment When `packages` is given, don't do anything
    dist = Distribution({**attrs, "packages": ["explicit_package"]})
    dist.set_defaults()
    assert not dist.py_modules
    assert set(dist.packages) == {"explicit_package"}


@pytest.mark.parametrize(
    ('dist_name', 'package_dir', 'package_files'),
    [
        ("my.pkg.nested", None, ["my/pkg/nested/__init__.py"]),
        ("my.pkg", None, ["my/pkg/__init__.py", "my/pkg/file.py"]),
        ("my_pkg", None, ["my_pkg.py"]),
        ("my_pkg", None, ["my_pkg/__init__.py", "my_pkg/nested/__init__.py"]),
        ("my_pkg", None, ["src/my_pkg/__init__.py", "src/my_pkg/nested/__init__.py"]),
        (
            "my_pkg",
            {"my_pkg": "lib", "my_pkg.lib2": "lib2"},
            ["lib/__init__.py", "lib/nested/__init__.pyt", "lib2/__init__.py"],
        ),
        # 045361.python.test_dist.line260.comment Should not try to guess a name from multiple py_modules/packages
        ("UNKNOWN", None, ["src/mod1.py", "src/mod2.py"]),
        ("UNKNOWN", None, ["src/pkg1/__ini__.py", "src/pkg2/__init__.py"]),
    ],
)
def test_dist_default_name(tmp_path, dist_name, package_dir, package_files):
    """Make sure dist.name is discovered from packages/py_modules"""
    ensure_files(tmp_path, package_files)
    attrs = {
        **EXAMPLE_BASE_INFO,
        "src_root": "/".join(os.path.split(tmp_path)),  # POSIX-style
        "package_dir": package_dir,
    }
    del attrs["name"]

    dist = Distribution(attrs)
    dist.set_defaults()
    assert dist.py_modules or dist.packages
    assert dist.get_name() == dist_name
