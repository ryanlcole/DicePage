# 007945.python.hook-jaraco.functools.line1.comment -----------------------------------------------------------------------------
# 007946.python.hook-jaraco.functools.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007947.python.hook-jaraco.functools.line3.comment
# 007948.python.hook-jaraco.functools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007949.python.hook-jaraco.functools.line5.comment or later) with exception for distributing the bootloader.
# 007950.python.hook-jaraco.functools.line6.comment
# 007951.python.hook-jaraco.functools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007952.python.hook-jaraco.functools.line8.comment
# 007953.python.hook-jaraco.functools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007954.python.hook-jaraco.functools.line10.comment -----------------------------------------------------------------------------

# 007955.python.hook-jaraco.functools.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007956.python.hook-jaraco.functools.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007957.python.hook-jaraco.functools.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
