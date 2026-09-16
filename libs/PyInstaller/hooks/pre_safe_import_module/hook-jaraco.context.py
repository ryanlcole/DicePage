# 007931.python.hook-jaraco.context.line1.comment -----------------------------------------------------------------------------
# 007932.python.hook-jaraco.context.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007933.python.hook-jaraco.context.line3.comment
# 007934.python.hook-jaraco.context.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007935.python.hook-jaraco.context.line5.comment or later) with exception for distributing the bootloader.
# 007936.python.hook-jaraco.context.line6.comment
# 007937.python.hook-jaraco.context.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007938.python.hook-jaraco.context.line8.comment
# 007939.python.hook-jaraco.context.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007940.python.hook-jaraco.context.line10.comment -----------------------------------------------------------------------------

# 007941.python.hook-jaraco.context.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007942.python.hook-jaraco.context.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007943.python.hook-jaraco.context.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
