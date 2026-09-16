# 006041.python.hook-gi.repository.GtkChamplain.line1.comment -----------------------------------------------------------------------------
# 006042.python.hook-gi.repository.GtkChamplain.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006043.python.hook-gi.repository.GtkChamplain.line3.comment
# 006044.python.hook-gi.repository.GtkChamplain.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006045.python.hook-gi.repository.GtkChamplain.line5.comment or later) with exception for distributing the bootloader.
# 006046.python.hook-gi.repository.GtkChamplain.line6.comment
# 006047.python.hook-gi.repository.GtkChamplain.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006048.python.hook-gi.repository.GtkChamplain.line8.comment
# 006049.python.hook-gi.repository.GtkChamplain.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006050.python.hook-gi.repository.GtkChamplain.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GtkChamplain', '0.12')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
