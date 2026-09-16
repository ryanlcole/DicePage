# 006239.python.hook-lib2to3.line1.comment -----------------------------------------------------------------------------
# 006240.python.hook-lib2to3.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006241.python.hook-lib2to3.line3.comment
# 006242.python.hook-lib2to3.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006243.python.hook-lib2to3.line5.comment or later) with exception for distributing the bootloader.
# 006244.python.hook-lib2to3.line6.comment
# 006245.python.hook-lib2to3.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006246.python.hook-lib2to3.line8.comment
# 006247.python.hook-lib2to3.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006248.python.hook-lib2to3.line10.comment -----------------------------------------------------------------------------

# 006249.python.hook-lib2to3.line12.comment This is needed to bundle lib2to3 Grammars files

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('lib2to3')
