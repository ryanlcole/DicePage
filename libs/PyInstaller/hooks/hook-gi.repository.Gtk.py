# 006025.python.hook-gi.repository.Gtk.line1.comment -----------------------------------------------------------------------------
# 006026.python.hook-gi.repository.Gtk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006027.python.hook-gi.repository.Gtk.line3.comment
# 006028.python.hook-gi.repository.Gtk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006029.python.hook-gi.repository.Gtk.line5.comment or later) with exception for distributing the bootloader.
# 006030.python.hook-gi.repository.Gtk.line6.comment
# 006031.python.hook-gi.repository.Gtk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006032.python.hook-gi.repository.Gtk.line8.comment
# 006033.python.hook-gi.repository.Gtk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006034.python.hook-gi.repository.Gtk.line10.comment -----------------------------------------------------------------------------

import os
import os.path

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import get_hook_config
from PyInstaller.utils.hooks.gi import GiModuleInfo, collect_glib_etc_files, collect_glib_share_files, \
    collect_glib_translations


def hook(hook_api):
    module_info = GiModuleInfo('Gtk', '3.0', hook_api=hook_api)  # Pass hook_api to read version from hook config
    if not module_info.available:
        return

    binaries, datas, hiddenimports = module_info.collect_typelib_data()

    # 006036.python.hook-gi.repository.Gtk.line28.comment Collect fontconfig data
    datas += collect_glib_share_files('fontconfig')

    # 006037.python.hook-gi.repository.Gtk.line31.comment Icons, themes, translations
    icon_list = get_hook_config(hook_api, "gi", "icons")
    if icon_list is not None:
        for icon in icon_list:
            datas += collect_glib_share_files(os.path.join('icons', icon))
    else:
        datas += collect_glib_share_files('icons')

    # 006038.python.hook-gi.repository.Gtk.line39.comment Themes
    theme_list = get_hook_config(hook_api, "gi", "themes")
    if theme_list is not None:
        for theme in theme_list:
            datas += collect_glib_share_files(os.path.join('themes', theme))
    else:
        datas += collect_glib_share_files('themes')

    # 006039.python.hook-gi.repository.Gtk.line47.comment Translations
    lang_list = get_hook_config(hook_api, "gi", "languages")
    datas += collect_glib_translations(f'gtk{module_info.version[0]}0', lang_list)

    # 006040.python.hook-gi.repository.Gtk.line51.comment These only seem to be required on Windows
    if is_win:
        datas += collect_glib_etc_files('fonts')
        datas += collect_glib_etc_files('pango')
        datas += collect_glib_share_files('fonts')

    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
