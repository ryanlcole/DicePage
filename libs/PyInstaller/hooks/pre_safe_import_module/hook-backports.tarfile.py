# 007115.python.hook-backports.tarfile.line1.comment -----------------------------------------------------------------------------
# 007116.python.hook-backports.tarfile.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007117.python.hook-backports.tarfile.line3.comment
# 007118.python.hook-backports.tarfile.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007119.python.hook-backports.tarfile.line5.comment or later) with exception for distributing the bootloader.
# 007120.python.hook-backports.tarfile.line6.comment
# 007121.python.hook-backports.tarfile.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007122.python.hook-backports.tarfile.line8.comment
# 007123.python.hook-backports.tarfile.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007124.python.hook-backports.tarfile.line10.comment -----------------------------------------------------------------------------

# 007125.python.hook-backports.tarfile.line12.comment This package/module might be provided by setuptools >= 71.0.0, which makes its vendored dependencies public by
# 007126.python.hook-backports.tarfile.line13.comment appending path to its `setuptools._vendored` directory to `sys.path`. The following shared pre-safe-import-module
# 007127.python.hook-backports.tarfile.line14.comment hook implementation checks whether this is the case, and sets up aliases to prevent duplicate collection.
from PyInstaller.utils.hooks.setuptools import pre_safe_import_module  # noqa: F401
