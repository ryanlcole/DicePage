# 006408.python.hook-numpy.line1.comment -----------------------------------------------------------------------------
# 006409.python.hook-numpy.line2.comment Copyright (c) 2013-2024, PyInstaller Development Team.
# 006410.python.hook-numpy.line3.comment
# 006411.python.hook-numpy.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006412.python.hook-numpy.line5.comment or later) with exception for distributing the bootloader. Additional
# 006413.python.hook-numpy.line6.comment
# 006414.python.hook-numpy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006415.python.hook-numpy.line8.comment
# 006416.python.hook-numpy.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006417.python.hook-numpy.line10.comment -----------------------------------------------------------------------------

# 006418.python.hook-numpy.line12.comment --- Copyright Disclaimer ---
# 006419.python.hook-numpy.line13.comment
# 006420.python.hook-numpy.line14.comment An earlier copy of this hook has been submitted to the NumPy project, where it was integrated in v1.23.0rc1
# 006421.python.hook-numpy.line15.comment (https://github.com/numpy/numpy/pull/20745), under terms and conditions outlined in their repository [1].
# 006422.python.hook-numpy.line16.comment
# 006423.python.hook-numpy.line17.comment A special provision is hereby granted to the NumPy project that allows the NumPy copy of the hook to incorporate the
# 006424.python.hook-numpy.line18.comment changes made to this (PyInstaller's) copy of the hook, subject to their licensing terms as opposed to PyInstaller's
# 006425.python.hook-numpy.line19.comment (stricter) licensing terms.
# 006426.python.hook-numpy.line20.comment
# 006427.python.hook-numpy.line21.comment .. refs:
# 006428.python.hook-numpy.line22.comment
# 006429.python.hook-numpy.line23.comment [1] NumPy's license: https://github.com/numpy/numpy/blob/master/LICENSE.txt

# 006430.python.hook-numpy.line25.comment NOTE: when comparing the contents of this hook and the NumPy version of the hook (for example, to port changes), keep
# 006431.python.hook-numpy.line26.comment in mind that this copy is PyInstaller-centric - it caters to the version of PyInstaller it is bundled with, but needs
# 006432.python.hook-numpy.line27.comment to account for different behavior of different NumPy versions. In contrast, the NumPy copy of the hook caters to the
# 006433.python.hook-numpy.line28.comment version of NumPy it is bundled with, but should account for behavior differences in different PyInstaller versions.

# 006434.python.hook-numpy.line30.comment Override the default hook priority so that our copy of hook is used instead of NumPy's one (which has priority 0,
# 006435.python.hook-numpy.line31.comment the default for upstream hooks).
# 006436.python.hook-numpy.line32.comment $PyInstaller-Hook-Priority: 1

from PyInstaller import compat
from PyInstaller.utils.hooks import (
    get_installer,
    collect_dynamic_libs,
)

from packaging.version import Version

numpy_version = Version(compat.importlib_metadata.version("numpy")).release
numpy_installer = get_installer('numpy')

hiddenimports = []
datas = []
binaries = []

# 006437.python.hook-numpy.line49.comment Collect shared libraries that are bundled inside the numpy's package directory. With PyInstaller 6.x, the directory
# 006438.python.hook-numpy.line50.comment layout of collected shared libraries should be preserved (to match behavior of the binary dependency analysis). In
# 006439.python.hook-numpy.line51.comment earlier versions of PyInstaller, it was necessary to collect the shared libraries into application's top-level
# 006440.python.hook-numpy.line52.comment directory (because that was also what binary dependency analysis in PyInstaller < 6.0 did).
binaries += collect_dynamic_libs("numpy")

# 006441.python.hook-numpy.line55.comment Check if we are using Anaconda-packaged numpy
if numpy_installer == 'conda':
    # 006442.python.hook-numpy.line57.comment Collect DLLs for NumPy and its dependencies (MKL, OpenBlas, OpenMP, etc.) from the communal Conda bin directory.
    from PyInstaller.utils.hooks import conda_support
    datas += conda_support.collect_dynamic_libs("numpy", dependencies=True)

# 006443.python.hook-numpy.line61.comment NumPy 1.26 started using `delvewheel` for its Windows PyPI wheels. While contemporary PyInstaller versions
# 006444.python.hook-numpy.line62.comment automatically pick up DLLs from external `numpy.libs` directory, this does not work on Anaconda python 3.8 and 3.9
# 006445.python.hook-numpy.line63.comment due to defunct `os.add_dll_directory`, which forces `delvewheel` to use the old load-order file approach. So we need
# 006446.python.hook-numpy.line64.comment to explicitly ensure that load-order file as well as DLLs are collected.
if compat.is_win and numpy_version >= (1, 26) and numpy_installer == 'pip':
    from PyInstaller.utils.hooks import collect_delvewheel_libs_directory
    datas, binaries = collect_delvewheel_libs_directory("numpy", datas=datas, binaries=binaries)

# 006447.python.hook-numpy.line69.comment Submodules PyInstaller cannot detect (probably because they are only imported by extension modules, which PyInstaller
# 006448.python.hook-numpy.line70.comment cannot read).
if numpy_version >= (2, 0):
    # 006449.python.hook-numpy.line72.comment In v2.0.0, `numpy.core` was renamed to `numpy._core`.
    # 006450.python.hook-numpy.line73.comment See https://github.com/numpy/numpy/commit/47b70cbffd672849a5d3b9b6fa6e515700460fd0
    hiddenimports += ['numpy._core._dtype_ctypes', 'numpy._core._multiarray_tests']
else:
    hiddenimports += ['numpy.core._dtype_ctypes']

    # 006451.python.hook-numpy.line78.comment See https://github.com/numpy/numpy/commit/99104bd2d0557078d7ea9a590129c87dd63df623
    if numpy_version >= (1, 25):
        hiddenimports += ['numpy.core._multiarray_tests']

# 006452.python.hook-numpy.line82.comment Starting with v2.3.0, we need to add `numpy._core._exceptions` to hiddenimports; in previous versions, this module
# 006453.python.hook-numpy.line83.comment was picked up due to explicit import in `numpy._core._methods`, which was removed as part of cleanup in
# 006454.python.hook-numpy.line84.comment https://github.com/numpy/numpy/commit/a51a4f5c10aa9b7962ff1e7e9b5f9b7d91c51489
if numpy_version >= (2, 3, 0):
    hiddenimports += ['numpy._core._exceptions']

# 006455.python.hook-numpy.line88.comment This hidden import was removed from NumPy hook in v1.25.0 (https://github.com/numpy/numpy/pull/22666). According to
# 006456.python.hook-numpy.line89.comment comment in the linked PR, it should have been unnecessary since v1.19.
if compat.is_conda and numpy_version < (1, 19):
    hiddenimports += ["six"]

# 006457.python.hook-numpy.line93.comment Remove testing and building code and packages that are referenced throughout NumPy but are not really dependencies.
excludedimports = [
    "scipy",
    "pytest",
    "nose",
    "f2py",
    "setuptools",
]

# 006458.python.hook-numpy.line102.comment As of v1.22.0, numpy.testing (imported for example by some scipy modules) requires numpy.distutils and distutils.
# 006459.python.hook-numpy.line103.comment This was due to numpy.testing adding import of numpy.testing._private.extbuild, which in turn imported numpy.distutils
# 006460.python.hook-numpy.line104.comment and distutils. These imports were moved into functions that require them in v1.22.2 and v.1.23.0.
# 006461.python.hook-numpy.line105.comment See: https://github.com/numpy/numpy/pull/20831 and https://github.com/numpy/numpy/pull/20906
# 006462.python.hook-numpy.line106.comment So we can exclude them for all numpy versions except for v1.22.0 and v1.22.1 - the main motivation is to avoid pulling
# 006463.python.hook-numpy.line107.comment in `setuptools` (which nowadays provides its vendored version of `distutils`).
if numpy_version < (1, 22, 0) or numpy_version > (1, 22, 1):
    excludedimports += [
        "distutils",
        "numpy.distutils",
    ]

# 006464.python.hook-numpy.line114.comment In numpy v2.0.0, numpy.f2py submodule has been added to numpy's `__all__` attribute. Therefore, using
# 006465.python.hook-numpy.line115.comment `from numpy import *` leads to an error if `numpy.f2py` is excluded (seen in scipy 1.14). The exclusion in earlier
# 006466.python.hook-numpy.line116.comment releases was not reported to cause any issues, so keep it around. Although it should be noted that it does break an
# 006467.python.hook-numpy.line117.comment explicit import (i.e., `import numpy.f2py`) from user's code as well, because it prevents collection of other
# 006468.python.hook-numpy.line118.comment submodules from `numpy.f2py`.
if numpy_version < (2, 0):
    excludedimports += [
        "numpy.f2py",
    ]
