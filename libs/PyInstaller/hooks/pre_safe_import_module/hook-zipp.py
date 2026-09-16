# 008136.python.hook-zipp.line1.comment -----------------------------------------------------------------------------
# 008137.python.hook-zipp.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008138.python.hook-zipp.line3.comment
# 008139.python.hook-zipp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008140.python.hook-zipp.line5.comment or later) with exception for distributing the bootloader.
# 008141.python.hook-zipp.line6.comment
# 008142.python.hook-zipp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008143.python.hook-zipp.line8.comment
# 008144.python.hook-zipp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008145.python.hook-zipp.line10.comment -----------------------------------------------------------------------------

# 008146.python.hook-zipp.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008147.python.hook-zipp.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008148.python.hook-zipp.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
