# 006814.python.hook-setuptools._vendor.jaraco.text.line1.comment -----------------------------------------------------------------------------
# 006815.python.hook-setuptools._vendor.jaraco.text.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006816.python.hook-setuptools._vendor.jaraco.text.line3.comment
# 006817.python.hook-setuptools._vendor.jaraco.text.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006818.python.hook-setuptools._vendor.jaraco.text.line5.comment or later) with exception for distributing the bootloader.
# 006819.python.hook-setuptools._vendor.jaraco.text.line6.comment
# 006820.python.hook-setuptools._vendor.jaraco.text.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006821.python.hook-setuptools._vendor.jaraco.text.line8.comment
# 006822.python.hook-setuptools._vendor.jaraco.text.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006823.python.hook-setuptools._vendor.jaraco.text.line10.comment -----------------------------------------------------------------------------

import fnmatch
from PyInstaller.utils.hooks.setuptools import setuptools_info

# 006824.python.hook-setuptools._vendor.jaraco.text.line15.comment Use cached data files list from setuptools_info, and extract relevant bits (to avoid having to call another
# 006825.python.hook-setuptools._vendor.jaraco.text.line16.comment `collect_data_files` and import `setuptools` in isolated process).
datas = [(src_name, dest_name) for src_name, dest_name in setuptools_info.vendored_data
         if fnmatch.fnmatch(src_name, "**/setuptools/_vendor/jaraco/text/*")]
