# 008015.python.hook-platformdirs.line1.comment -----------------------------------------------------------------------------
# 008016.python.hook-platformdirs.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008017.python.hook-platformdirs.line3.comment
# 008018.python.hook-platformdirs.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008019.python.hook-platformdirs.line5.comment or later) with exception for distributing the bootloader.
# 008020.python.hook-platformdirs.line6.comment
# 008021.python.hook-platformdirs.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008022.python.hook-platformdirs.line8.comment
# 008023.python.hook-platformdirs.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008024.python.hook-platformdirs.line10.comment -----------------------------------------------------------------------------

# 008025.python.hook-platformdirs.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008026.python.hook-platformdirs.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008027.python.hook-platformdirs.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
