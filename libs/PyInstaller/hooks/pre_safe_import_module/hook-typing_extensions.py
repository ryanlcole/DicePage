# 008095.python.hook-typing_extensions.line1.comment -----------------------------------------------------------------------------
# 008096.python.hook-typing_extensions.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008097.python.hook-typing_extensions.line3.comment
# 008098.python.hook-typing_extensions.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008099.python.hook-typing_extensions.line5.comment or later) with exception for distributing the bootloader.
# 008100.python.hook-typing_extensions.line6.comment
# 008101.python.hook-typing_extensions.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008102.python.hook-typing_extensions.line8.comment
# 008103.python.hook-typing_extensions.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008104.python.hook-typing_extensions.line10.comment -----------------------------------------------------------------------------

# 008105.python.hook-typing_extensions.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008106.python.hook-typing_extensions.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008107.python.hook-typing_extensions.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
