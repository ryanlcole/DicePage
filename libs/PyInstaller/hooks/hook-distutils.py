# 005330.python.hook-distutils.line1.comment -----------------------------------------------------------------------------
# 005331.python.hook-distutils.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005332.python.hook-distutils.line3.comment
# 005333.python.hook-distutils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005334.python.hook-distutils.line5.comment or later) with exception for distributing the bootloader.
# 005335.python.hook-distutils.line6.comment
# 005336.python.hook-distutils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005337.python.hook-distutils.line8.comment
# 005338.python.hook-distutils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005339.python.hook-distutils.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.setuptools import setuptools_info

hiddenimports = []

# 005340.python.hook-distutils.line16.comment From Python 3.6 and later ``distutils.sysconfig`` takes on the same behaviour as regular ``sysconfig`` of moving the
# 005341.python.hook-distutils.line17.comment config vars to a module (see hook-sysconfig.py). It doesn't use a nice `get module name` function like ``sysconfig``
# 005342.python.hook-distutils.line18.comment does to help us locate it but the module is the same file that ``sysconfig`` uses so we can use the
# 005343.python.hook-distutils.line19.comment ``_get_sysconfigdata_name()`` from regular ``sysconfig``.
try:
    import sysconfig
    hiddenimports += [sysconfig._get_sysconfigdata_name()]
except AttributeError:
    # 005344.python.hook-distutils.line24.comment Either sysconfig has no attribute _get_sysconfigdata_name (i.e., the function does not exist), or this is Windows
    # 005345.python.hook-distutils.line25.comment and the _get_sysconfigdata_name() call failed due to missing sys.abiflags attribute.
    pass

# 005346.python.hook-distutils.line28.comment Starting with setuptools 60.0, the vendored distutils overrides the stdlib one (which will be removed in python 3.12
# 005347.python.hook-distutils.line29.comment anyway), so check if we are using that version. While the distutils override behavior can be controleld via the
# 005348.python.hook-distutils.line30.comment ``SETUPTOOLS_USE_DISTUTILS`` environment variable, the latter may have a different value during the build and at the
# 005349.python.hook-distutils.line31.comment runtime, and so we need to ensure that both stdlib and setuptools variant of distutils are collected.
if setuptools_info.available and setuptools_info.version >= (60, 0):
    hiddenimports += ['setuptools._distutils']
