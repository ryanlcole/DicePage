# 007129.python.hook-distutils.line1.comment -----------------------------------------------------------------------------
# 007130.python.hook-distutils.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 007131.python.hook-distutils.line3.comment
# 007132.python.hook-distutils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007133.python.hook-distutils.line5.comment or later) with exception for distributing the bootloader.
# 007134.python.hook-distutils.line6.comment
# 007135.python.hook-distutils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007136.python.hook-distutils.line8.comment
# 007137.python.hook-distutils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007138.python.hook-distutils.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat
from PyInstaller.utils.hooks.setuptools import setuptools_info


def pre_safe_import_module(api):
    # 007139.python.hook-distutils.line17.comment `distutils` was removed from from stdlib in python 3.12; if it is available, it is provided by `setuptools`.
    # 007140.python.hook-distutils.line18.comment Therefore, we need to create package/module alias entries, which prevent the setuptools._distutils` and its
    # 007141.python.hook-distutils.line19.comment submodules from being collected as top-level modules (as `distutils` and its submodules) in addition to being
    # 007142.python.hook-distutils.line20.comment collected as their "true" names.
    if compat.is_py312 and setuptools_info.distutils_vendored:
        for aliased_name, real_vendored_name in setuptools_info.get_distutils_aliases():
            api.add_alias_module(real_vendored_name, aliased_name)
