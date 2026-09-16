# 007889.python.hook-importlib_metadata.line1.comment -----------------------------------------------------------------------------
# 007890.python.hook-importlib_metadata.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007891.python.hook-importlib_metadata.line3.comment
# 007892.python.hook-importlib_metadata.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007893.python.hook-importlib_metadata.line5.comment or later) with exception for distributing the bootloader.
# 007894.python.hook-importlib_metadata.line6.comment
# 007895.python.hook-importlib_metadata.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007896.python.hook-importlib_metadata.line8.comment
# 007897.python.hook-importlib_metadata.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007898.python.hook-importlib_metadata.line10.comment -----------------------------------------------------------------------------

# 007899.python.hook-importlib_metadata.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007900.python.hook-importlib_metadata.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007901.python.hook-importlib_metadata.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
