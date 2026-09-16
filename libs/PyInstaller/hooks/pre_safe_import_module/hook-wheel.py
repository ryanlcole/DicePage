# 008122.python.hook-wheel.line1.comment -----------------------------------------------------------------------------
# 008123.python.hook-wheel.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008124.python.hook-wheel.line3.comment
# 008125.python.hook-wheel.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008126.python.hook-wheel.line5.comment or later) with exception for distributing the bootloader.
# 008127.python.hook-wheel.line6.comment
# 008128.python.hook-wheel.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008129.python.hook-wheel.line8.comment
# 008130.python.hook-wheel.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008131.python.hook-wheel.line10.comment -----------------------------------------------------------------------------

# 008132.python.hook-wheel.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008133.python.hook-wheel.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008134.python.hook-wheel.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
