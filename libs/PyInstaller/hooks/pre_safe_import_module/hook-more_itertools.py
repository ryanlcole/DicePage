# 007973.python.hook-more_itertools.line1.comment -----------------------------------------------------------------------------
# 007974.python.hook-more_itertools.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007975.python.hook-more_itertools.line3.comment
# 007976.python.hook-more_itertools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007977.python.hook-more_itertools.line5.comment or later) with exception for distributing the bootloader.
# 007978.python.hook-more_itertools.line6.comment
# 007979.python.hook-more_itertools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007980.python.hook-more_itertools.line8.comment
# 007981.python.hook-more_itertools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007982.python.hook-more_itertools.line10.comment -----------------------------------------------------------------------------

# 007983.python.hook-more_itertools.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007984.python.hook-more_itertools.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007985.python.hook-more_itertools.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
