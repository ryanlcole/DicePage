# 006061.python.hook-gi.repository.GtkSource.line1.comment -----------------------------------------------------------------------------
# 006062.python.hook-gi.repository.GtkSource.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006063.python.hook-gi.repository.GtkSource.line3.comment
# 006064.python.hook-gi.repository.GtkSource.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006065.python.hook-gi.repository.GtkSource.line5.comment or later) with exception for distributing the bootloader.
# 006066.python.hook-gi.repository.GtkSource.line6.comment
# 006067.python.hook-gi.repository.GtkSource.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006068.python.hook-gi.repository.GtkSource.line8.comment
# 006069.python.hook-gi.repository.GtkSource.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006070.python.hook-gi.repository.GtkSource.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo, collect_glib_share_files


def hook(hook_api):
    module_info = GiModuleInfo('GtkSource', '3.0', hook_api=hook_api)  # Pass hook_api to read version from hook config
    if not module_info.available:
        return

    binaries, datas, hiddenimports = module_info.collect_typelib_data()

    # 006072.python.hook-gi.repository.GtkSource.line22.comment Collect data files
    # 006073.python.hook-gi.repository.GtkSource.line23.comment The data directory name contains verbatim version, e.g.:
    # 006074.python.hook-gi.repository.GtkSource.line24.comment * GtkSourceView-3.0 -> /usr/share/gtksourceview-3.0
    # 006075.python.hook-gi.repository.GtkSource.line25.comment * GtkSourceView-4 -> /usr/share/gtksourceview-4
    # 006076.python.hook-gi.repository.GtkSource.line26.comment * GtkSourceView-5 -> /usr/share/gtksourceview-5
    datas += collect_glib_share_files(f'gtksourceview-{module_info.version}')

    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
