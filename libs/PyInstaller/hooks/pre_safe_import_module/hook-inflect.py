# 007917.python.hook-inflect.line1.comment -----------------------------------------------------------------------------
# 007918.python.hook-inflect.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007919.python.hook-inflect.line3.comment
# 007920.python.hook-inflect.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007921.python.hook-inflect.line5.comment or later) with exception for distributing the bootloader.
# 007922.python.hook-inflect.line6.comment
# 007923.python.hook-inflect.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007924.python.hook-inflect.line8.comment
# 007925.python.hook-inflect.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007926.python.hook-inflect.line10.comment -----------------------------------------------------------------------------

# 007927.python.hook-inflect.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007928.python.hook-inflect.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007929.python.hook-inflect.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
