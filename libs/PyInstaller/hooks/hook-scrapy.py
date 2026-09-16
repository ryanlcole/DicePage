# 006788.python.hook-scrapy.line1.comment -----------------------------------------------------------------------------
# 006789.python.hook-scrapy.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006790.python.hook-scrapy.line3.comment
# 006791.python.hook-scrapy.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006792.python.hook-scrapy.line5.comment or later) with exception for distributing the bootloader.
# 006793.python.hook-scrapy.line6.comment
# 006794.python.hook-scrapy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006795.python.hook-scrapy.line8.comment
# 006796.python.hook-scrapy.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006797.python.hook-scrapy.line10.comment -----------------------------------------------------------------------------

# 006798.python.hook-scrapy.line12.comment Hook for https://pypi.org/project/Scrapy/
# 006799.python.hook-scrapy.line13.comment https://stackoverflow.com/questions/49085970/no-such-file-or-directory-error-using-pyinstaller-and-scrapy

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files('scrapy')
hiddenimports = collect_submodules('scrapy')
