# 045125.python.test_pip_install_sdist.line1.comment https://github.com/python/mypy/issues/16936
# 045126.python.test_pip_install_sdist.line2.comment mypy: disable-error-code="has-type"
"""Integration tests for setuptools that focus on building packages via pip.

The idea behind these tests is not to exhaustively check all the possible
combinations of packages, operating systems, supporting libraries, etc, but
rather check a limited number of popular packages and how they interact with
the exposed public API. This way if any change in API is introduced, we hope to
identify backward compatibility problems before publishing a release.

The number of tested packages is purposefully kept small, to minimise duration
and the associated maintenance cost (changes in the way these packages define
their build process may require changes in the tests).
"""

import json
import os
import shutil
import sys
from enum import Enum
from glob import glob
from hashlib import md5
from urllib.request import urlopen

import pytest
from packaging.requirements import Requirement

from .helpers import Archive, run

pytestmark = pytest.mark.integration


(LATEST,) = Enum("v", "LATEST")  # type: ignore[misc] # https://github.com/python/mypy/issues/16936
"""Default version to be checked"""
# 045128.python.test_pip_install_sdist.line35.comment There are positive and negative aspects of checking the latest version of the
# 045129.python.test_pip_install_sdist.line36.comment packages.
# 045130.python.test_pip_install_sdist.line37.comment The main positive aspect is that the latest version might have already
# 045131.python.test_pip_install_sdist.line38.comment removed the use of APIs deprecated in previous releases of setuptools.


# 045132.python.test_pip_install_sdist.line41.comment Packages to be tested:
# 045133.python.test_pip_install_sdist.line42.comment (Please notice the test environment cannot support EVERY library required for
# 045134.python.test_pip_install_sdist.line43.comment compiling binary extensions. In Ubuntu/Debian nomenclature, we only assume
# 045135.python.test_pip_install_sdist.line44.comment that `build-essential`, `gfortran` and `libopenblas-dev` are installed,
# 045136.python.test_pip_install_sdist.line45.comment due to their relevance to the numerical/scientific programming ecosystem)
EXAMPLES = [
    ("pip", LATEST),  # just in case...
    ("pytest", LATEST),  # uses setuptools_scm
    ("mypy", LATEST),  # custom build_py + ext_modules
    # 045140.python.test_pip_install_sdist.line50.comment --- Popular packages: https://hugovk.github.io/top-pypi-packages/ ---
    ("botocore", LATEST),
    ("kiwisolver", LATEST),  # build_ext
    ("brotli", LATEST),  # not in the list but used by urllib3
    ("pyyaml", LATEST),  # cython + custom build_ext + custom distclass
    ("charset-normalizer", LATEST),  # uses mypyc, used by aiohttp
    ("protobuf", LATEST),
    # 045145.python.test_pip_install_sdist.line57.comment ("requests", LATEST),  # XXX: https://github.com/psf/requests/pull/6920
    ("celery", LATEST),
    # 045146.python.test_pip_install_sdist.line59.comment When adding packages to this list, make sure they expose a `__version__`
    # 045147.python.test_pip_install_sdist.line60.comment attribute, or modify the tests below
]


# 045148.python.test_pip_install_sdist.line64.comment Some packages have "optional" dependencies that modify their build behaviour
# 045149.python.test_pip_install_sdist.line65.comment and are not listed in pyproject.toml, others still use `setup_requires`
EXTRA_BUILD_DEPS = {
    "pyyaml": ("Cython<3.0",),  # constraint to avoid errors
    "charset-normalizer": ("mypy>=1.4.1",),  # no pyproject.toml available
}

EXTRA_ENV_VARS = {
    "pyyaml": {"PYYAML_FORCE_CYTHON": "1"},
    "charset-normalizer": {"CHARSET_NORMALIZER_USE_MYPYC": "1"},
}

IMPORT_NAME = {
    "pyyaml": "yaml",
    "protobuf": "google.protobuf",
}


VIRTUALENV = (sys.executable, "-m", "virtualenv")


# 045152.python.test_pip_install_sdist.line85.comment By default, pip will try to build packages in isolation (PEP 517), which
# 045153.python.test_pip_install_sdist.line86.comment means it will download the previous stable version of setuptools.
# 045154.python.test_pip_install_sdist.line87.comment `pip` flags can avoid that (the version of setuptools under test
# 045155.python.test_pip_install_sdist.line88.comment should be the one to be used)
INSTALL_OPTIONS = (
    "--ignore-installed",
    "--no-build-isolation",
    # 045156.python.test_pip_install_sdist.line92.comment Omit "--no-binary :all:" the sdist is supplied directly.
    # 045157.python.test_pip_install_sdist.line93.comment Allows dependencies as wheels.
)
# 045158.python.test_pip_install_sdist.line95.comment The downside of `--no-build-isolation` is that pip will not download build
# 045159.python.test_pip_install_sdist.line96.comment dependencies. The test script will have to also handle that.


@pytest.fixture
def venv_python(tmp_path):
    run([*VIRTUALENV, str(tmp_path / ".venv")])
    possible_path = (str(p.parent) for p in tmp_path.glob(".venv/*/python*"))
    return shutil.which("python", path=os.pathsep.join(possible_path))


@pytest.fixture(autouse=True)
def _prepare(tmp_path, venv_python, monkeypatch):
    download_path = os.getenv("DOWNLOAD_PATH", str(tmp_path))
    os.makedirs(download_path, exist_ok=True)

    # 045160.python.test_pip_install_sdist.line111.comment Environment vars used for building some of the packages
    monkeypatch.setenv("USE_MYPYC", "1")

    yield

    # 045161.python.test_pip_install_sdist.line116.comment Let's provide the maximum amount of information possible in the case
    # 045162.python.test_pip_install_sdist.line117.comment it is necessary to debug the tests directly from the CI logs.
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Temporary directory:")
    map(print, tmp_path.glob("*"))
    print("Virtual environment:")
    run([venv_python, "-m", "pip", "freeze"])


@pytest.mark.parametrize(("package", "version"), EXAMPLES)
@pytest.mark.uses_network
def test_install_sdist(package, version, tmp_path, venv_python, setuptools_wheel):
    venv_pip = (venv_python, "-m", "pip")
    sdist = retrieve_sdist(package, version, tmp_path)
    deps = build_deps(package, sdist)
    if deps:
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Dependencies:", deps)
        run([*venv_pip, "install", *deps])

    # 045163.python.test_pip_install_sdist.line136.comment Use a virtualenv to simulate PEP 517 isolation
    # 045164.python.test_pip_install_sdist.line137.comment but install fresh setuptools wheel to ensure the version under development
    env = EXTRA_ENV_VARS.get(package, {})
    run([*venv_pip, "install", "--force-reinstall", setuptools_wheel])
    run([*venv_pip, "install", *INSTALL_OPTIONS, sdist], env)

    # 045165.python.test_pip_install_sdist.line142.comment Execute a simple script to make sure the package was installed correctly
    pkg = IMPORT_NAME.get(package, package).replace("-", "_")
    script = f"import {pkg}; print(getattr({pkg}, '__version__', 0))"
    run([venv_python, "-c", script])


# 045166.python.test_pip_install_sdist.line148.comment ---- Helper Functions ----


def retrieve_sdist(package, version, tmp_path):
    """Either use cached sdist file or download it from PyPI"""
    # 045167.python.test_pip_install_sdist.line153.comment `pip download` cannot be used due to
    # 045168.python.test_pip_install_sdist.line154.comment https://github.com/pypa/pip/issues/1884
    # 045169.python.test_pip_install_sdist.line155.comment https://discuss.python.org/t/pep-625-file-name-of-a-source-distribution/4686
    # 045170.python.test_pip_install_sdist.line156.comment We have to find the correct distribution file and download it
    download_path = os.getenv("DOWNLOAD_PATH", str(tmp_path))
    dist = retrieve_pypi_sdist_metadata(package, version)

    # 045171.python.test_pip_install_sdist.line160.comment Remove old files to prevent cache to grow indefinitely
    for file in glob(os.path.join(download_path, f"{package}*")):
        if dist["filename"] != file:
            os.unlink(file)

    dist_file = os.path.join(download_path, dist["filename"])
    if not os.path.exists(dist_file):
        download(dist["url"], dist_file, dist["md5_digest"])
    return dist_file


def retrieve_pypi_sdist_metadata(package, version):
    # 045172.python.test_pip_install_sdist.line172.comment https://warehouse.pypa.io/api-reference/json.html
    id_ = package if version is LATEST else f"{package}/{version}"
    with urlopen(f"https://pypi.org/pypi/{id_}/json") as f:
        metadata = json.load(f)

    if metadata["info"]["yanked"]:
        raise ValueError(f"Release for {package} {version} was yanked")

    version = metadata["info"]["version"]
    release = metadata["releases"][version] if version is LATEST else metadata["urls"]
    (sdist,) = filter(lambda d: d["packagetype"] == "sdist", release)
    return sdist


def download(url, dest, md5_digest):
    with urlopen(url) as f:
        data = f.read()

    assert md5(data).hexdigest() == md5_digest

    with open(dest, "wb") as f:
        f.write(data)

    assert os.path.exists(dest)


def build_deps(package, sdist_file):
    """Find out what are the build dependencies for a package.

    "Manually" install them, since pip will not install build
    deps with `--no-build-isolation`.
    """
    # 045173.python.test_pip_install_sdist.line204.comment delay importing, since pytest discovery phase may hit this file from a
    # 045174.python.test_pip_install_sdist.line205.comment testenv without tomli
    from setuptools.compat.py310 import tomllib

    archive = Archive(sdist_file)
    info = tomllib.loads(_read_pyproject(archive))
    deps = info.get("build-system", {}).get("requires", [])
    deps += EXTRA_BUILD_DEPS.get(package, [])
    # 045175.python.test_pip_install_sdist.line212.comment Remove setuptools from requirements (and deduplicate)
    requirements = {Requirement(d).name: d for d in deps}
    return [v for k, v in requirements.items() if k != "setuptools"]


def _read_pyproject(archive):
    contents = (
        archive.get_content(member)
        for member in archive
        if os.path.basename(archive.get_name(member)) == "pyproject.toml"
    )
    return next(contents, "")
