# 008081.python.hook-typeguard.line1.comment -----------------------------------------------------------------------------
# 008082.python.hook-typeguard.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 008083.python.hook-typeguard.line3.comment
# 008084.python.hook-typeguard.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008085.python.hook-typeguard.line5.comment or later) with exception for distributing the bootloader.
# 008086.python.hook-typeguard.line6.comment
# 008087.python.hook-typeguard.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008088.python.hook-typeguard.line8.comment
# 008089.python.hook-typeguard.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008090.python.hook-typeguard.line10.comment -----------------------------------------------------------------------------

# 008091.python.hook-typeguard.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 008092.python.hook-typeguard.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 008093.python.hook-typeguard.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
