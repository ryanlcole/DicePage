# 005588.python.hook-gi.repository.GLib.line1.comment -----------------------------------------------------------------------------
# 005589.python.hook-gi.repository.GLib.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005590.python.hook-gi.repository.GLib.line3.comment
# 005591.python.hook-gi.repository.GLib.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005592.python.hook-gi.repository.GLib.line5.comment or later) with exception for distributing the bootloader.
# 005593.python.hook-gi.repository.GLib.line6.comment
# 005594.python.hook-gi.repository.GLib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005595.python.hook-gi.repository.GLib.line8.comment
# 005596.python.hook-gi.repository.GLib.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005597.python.hook-gi.repository.GLib.line10.comment -----------------------------------------------------------------------------

import glob
import os

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import get_hook_config
from PyInstaller.utils.hooks.gi import GiModuleInfo, collect_glib_share_files, collect_glib_translations


def hook(hook_api):
    module_info = GiModuleInfo('GLib', '2.0')
    if not module_info.available:
        return

    binaries, datas, hiddenimports = module_info.collect_typelib_data()

    # 005598.python.hook-gi.repository.GLib.line27.comment Collect translations
    lang_list = get_hook_config(hook_api, "gi", "languages")
    datas += collect_glib_translations('glib20', lang_list)

    # 005599.python.hook-gi.repository.GLib.line31.comment Collect schemas
    datas += collect_glib_share_files('glib-2.0', 'schemas')

    # 005600.python.hook-gi.repository.GLib.line34.comment On Windows, glib needs a spawn helper for g_spawn* API
    if is_win:
        pattern = os.path.join(module_info.get_libdir(), 'gspawn-*-helper*.exe')
        for f in glob.glob(pattern):
            binaries.append((f, '.'))

    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
