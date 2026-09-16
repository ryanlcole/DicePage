# 007101.python.hook-autocommand.line1.comment -----------------------------------------------------------------------------
# 007102.python.hook-autocommand.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007103.python.hook-autocommand.line3.comment
# 007104.python.hook-autocommand.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007105.python.hook-autocommand.line5.comment or later) with exception for distributing the bootloader.
# 007106.python.hook-autocommand.line6.comment
# 007107.python.hook-autocommand.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007108.python.hook-autocommand.line8.comment
# 007109.python.hook-autocommand.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007110.python.hook-autocommand.line10.comment -----------------------------------------------------------------------------

# 007111.python.hook-autocommand.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007112.python.hook-autocommand.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007113.python.hook-autocommand.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
