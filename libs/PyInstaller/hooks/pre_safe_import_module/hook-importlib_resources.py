# 007903.python.hook-importlib_resources.line1.comment -----------------------------------------------------------------------------
# 007904.python.hook-importlib_resources.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007905.python.hook-importlib_resources.line3.comment
# 007906.python.hook-importlib_resources.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007907.python.hook-importlib_resources.line5.comment or later) with exception for distributing the bootloader.
# 007908.python.hook-importlib_resources.line6.comment
# 007909.python.hook-importlib_resources.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007910.python.hook-importlib_resources.line8.comment
# 007911.python.hook-importlib_resources.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007912.python.hook-importlib_resources.line10.comment -----------------------------------------------------------------------------

# 007913.python.hook-importlib_resources.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007914.python.hook-importlib_resources.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007915.python.hook-importlib_resources.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
