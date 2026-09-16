# 007959.python.hook-jaraco.text.line1.comment -----------------------------------------------------------------------------
# 007960.python.hook-jaraco.text.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007961.python.hook-jaraco.text.line3.comment
# 007962.python.hook-jaraco.text.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007963.python.hook-jaraco.text.line5.comment or later) with exception for distributing the bootloader.
# 007964.python.hook-jaraco.text.line6.comment
# 007965.python.hook-jaraco.text.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007966.python.hook-jaraco.text.line8.comment
# 007967.python.hook-jaraco.text.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007968.python.hook-jaraco.text.line10.comment -----------------------------------------------------------------------------

# 007969.python.hook-jaraco.text.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007970.python.hook-jaraco.text.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007971.python.hook-jaraco.text.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
