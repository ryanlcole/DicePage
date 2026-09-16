# 007987.python.hook-ordered_set.line1.comment -----------------------------------------------------------------------------
# 007988.python.hook-ordered_set.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007989.python.hook-ordered_set.line3.comment
# 007990.python.hook-ordered_set.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007991.python.hook-ordered_set.line5.comment or later) with exception for distributing the bootloader.
# 007992.python.hook-ordered_set.line6.comment
# 007993.python.hook-ordered_set.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007994.python.hook-ordered_set.line8.comment
# 007995.python.hook-ordered_set.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007996.python.hook-ordered_set.line10.comment -----------------------------------------------------------------------------

# 007997.python.hook-ordered_set.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007998.python.hook-ordered_set.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007999.python.hook-ordered_set.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
