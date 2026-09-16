# 008067.python.hook-tomli.line1.comment -----------------------------------------------------------------------------
# 008068.python.hook-tomli.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008069.python.hook-tomli.line3.comment
# 008070.python.hook-tomli.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008071.python.hook-tomli.line5.comment or later) with exception for distributing the bootloader.
# 008072.python.hook-tomli.line6.comment
# 008073.python.hook-tomli.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008074.python.hook-tomli.line8.comment
# 008075.python.hook-tomli.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008076.python.hook-tomli.line10.comment -----------------------------------------------------------------------------

# 008077.python.hook-tomli.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008078.python.hook-tomli.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008079.python.hook-tomli.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
