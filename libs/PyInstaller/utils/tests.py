# 011145.python.tests.line1.comment -----------------------------------------------------------------------------
# 011146.python.tests.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 011147.python.tests.line3.comment
# 011148.python.tests.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 011149.python.tests.line5.comment or later) with exception for distributing the bootloader.
# 011150.python.tests.line6.comment
# 011151.python.tests.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 011152.python.tests.line8.comment
# 011153.python.tests.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 011154.python.tests.line10.comment -----------------------------------------------------------------------------
"""
Decorators for skipping PyInstaller tests when specific requirements are not met.
"""

import inspect
import sys
import textwrap

import pytest

from PyInstaller.utils.hooks import check_requirement

# 011155.python.tests.line23.comment Wrap some pytest decorators to be consistent in tests.
parametrize = pytest.mark.parametrize
skipif = pytest.mark.skipif
xfail = pytest.mark.xfail
skip = pytest.mark.skip

# 011156.python.tests.line29.comment Use these decorators to use the `pyi_builder` fixture only in onedir or only in onefile mode instead of both.
onedir_only = pytest.mark.parametrize('pyi_builder', ['onedir'], indirect=True)
onefile_only = pytest.mark.parametrize('pyi_builder', ['onefile'], indirect=True)


def importorskip(package: str):
    """
    Skip a decorated test if **package** is not importable.

    Arguments:
        package:
            The name of the module. May be anything that is allowed after the ``import`` keyword. e.g. 'numpy' or
            'PIL.Image'.
    Returns:
        A pytest marker which either skips the test or does nothing.

    This function intentionally does not import the module. Doing so can lead to `sys.path` and `PATH` being
    polluted, which then breaks later builds.
    """
    if not importable(package):
        return pytest.mark.skip(f"Can't import '{package}'.")
    return pytest.mark.skipif(False, reason=f"Don't skip: '{package}' is importable.")


def importable(package: str):
    from importlib.util import find_spec

    # 011157.python.tests.line56.comment The find_spec() function is used by the importlib machinery to locate a module to import. Using it finds the
    # 011158.python.tests.line57.comment module but does not run it. Unfortunately, it does import parent modules to check submodules.
    if "." in package:
        # 011159.python.tests.line59.comment Using subprocesses is slow. If the top level module doesn't exist then we can skip it.
        if not importable(package.split(".")[0]):
            return False
        # 011160.python.tests.line62.comment This is a submodule, import it in isolation.
        from subprocess import DEVNULL, run
        return run([sys.executable, "-c", "import " + package], stdout=DEVNULL, stderr=DEVNULL).returncode == 0

    return find_spec(package) is not None


def requires(requirement: str):
    """
    Mark a test to be skipped if **requirement** is not satisfied.

    Args:
        requirement:
            A distribution name and optional version specifier(s). See :func:`PyInstaller.utils.hooks.check_requirement`
            which this argument is forwarded to.
    Returns:
        Either a skip marker or a dummy marker.

    This function operates on distribution metadata, and does not import any modules.
    """
    if check_requirement(requirement):
        return pytest.mark.skipif(False, reason=f"Don't skip: '{requirement}' is satisfied.")
    else:
        return pytest.mark.skip(f"Requires {requirement}.")


def gen_sourcefile(tmp_path, source, test_id=None):
    """
    Generate a source file for testing.

    The source will be written into a file named like the test-function. This file will then be passed to
    `test_script`. If you need other related file, e.g. as `.toc`-file for testing the content, put it at at the
    normal place. Just mind to take the basnename from the test-function's name.

    :param script: Source code to create executable from. This will be saved into a temporary file which is then
                   passed on to `test_script`.

    :param test_id: Test-id for parametrized tests. If given, it will be appended to the script filename,
                    separated by two underscores.
    """
    testname = inspect.stack()[1][3]
    if test_id:
        # 011161.python.tests.line104.comment For parametrized test append the test-id.
        testname = testname + '__' + test_id

    # 011162.python.tests.line107.comment Periods are not allowed in Python module names.
    testname = testname.replace('.', '_')
    scriptfile = tmp_path / (testname + '.py')
    source = textwrap.dedent(source)
    scriptfile.write_text(source, encoding='utf-8')
    return scriptfile
