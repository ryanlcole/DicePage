# 008001.python.hook-packaging.line1.comment -----------------------------------------------------------------------------
# 008002.python.hook-packaging.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008003.python.hook-packaging.line3.comment
# 008004.python.hook-packaging.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008005.python.hook-packaging.line5.comment or later) with exception for distributing the bootloader.
# 008006.python.hook-packaging.line6.comment
# 008007.python.hook-packaging.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008008.python.hook-packaging.line8.comment
# 008009.python.hook-packaging.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008010.python.hook-packaging.line10.comment -----------------------------------------------------------------------------

# 008011.python.hook-packaging.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008012.python.hook-packaging.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008013.python.hook-packaging.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
