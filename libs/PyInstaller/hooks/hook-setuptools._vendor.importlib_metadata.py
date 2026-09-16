# 006800.python.hook-setuptools._vendor.importlib_metadata.line1.comment -----------------------------------------------------------------------------
# 006801.python.hook-setuptools._vendor.importlib_metadata.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006802.python.hook-setuptools._vendor.importlib_metadata.line3.comment
# 006803.python.hook-setuptools._vendor.importlib_metadata.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006804.python.hook-setuptools._vendor.importlib_metadata.line5.comment or later) with exception for distributing the bootloader.
# 006805.python.hook-setuptools._vendor.importlib_metadata.line6.comment
# 006806.python.hook-setuptools._vendor.importlib_metadata.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006807.python.hook-setuptools._vendor.importlib_metadata.line8.comment
# 006808.python.hook-setuptools._vendor.importlib_metadata.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006809.python.hook-setuptools._vendor.importlib_metadata.line10.comment -----------------------------------------------------------------------------

import fnmatch
from PyInstaller.utils.hooks.setuptools import setuptools_info

# 006810.python.hook-setuptools._vendor.importlib_metadata.line15.comment Collect metadata for setuptools-vendored copy of importlib-metadata, to match the behavior of hook for
# 006811.python.hook-setuptools._vendor.importlib_metadata.line16.comment stand-alone version of the package (i.e., `hook-importlib_metadata.py`).

# 006812.python.hook-setuptools._vendor.importlib_metadata.line18.comment Use cached data files list from setuptools_info, and extract relevant bits (to avoid having to call another
# 006813.python.hook-setuptools._vendor.importlib_metadata.line19.comment `collect_data_files` and import `setuptools` in isolated process).
datas = [(src_name, dest_name) for src_name, dest_name in setuptools_info.vendored_data
         if fnmatch.fnmatch(src_name, "**/setuptools/_vendor/importlib_metadata-*.dist-info/*")]
