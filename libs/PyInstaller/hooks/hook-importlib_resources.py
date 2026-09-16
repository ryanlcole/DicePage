# 006204.python.hook-importlib_resources.line1.comment -----------------------------------------------------------------------------
# 006205.python.hook-importlib_resources.line2.comment Copyright (c) 2019-2023, PyInstaller Development Team.
# 006206.python.hook-importlib_resources.line3.comment
# 006207.python.hook-importlib_resources.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006208.python.hook-importlib_resources.line5.comment or later) with exception for distributing the bootloader.
# 006209.python.hook-importlib_resources.line6.comment
# 006210.python.hook-importlib_resources.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006211.python.hook-importlib_resources.line8.comment
# 006212.python.hook-importlib_resources.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006213.python.hook-importlib_resources.line10.comment -----------------------------------------------------------------------------
"""
`importlib_resources` is a backport of the 3.9+ module `importlib.resources`
"""

from PyInstaller.utils.hooks import check_requirement, collect_data_files

# 006214.python.hook-importlib_resources.line17.comment Prior to v1.2.0, a `version.txt` file is used to set __version__. Later versions use `importlib.metadata`.
if check_requirement("importlib_resources < 1.2.0"):
    datas = collect_data_files("importlib_resources", includes=["version.txt"])

if check_requirement("importlib_resources >= 1.3.1"):
    hiddenimports = ['importlib_resources.trees']
