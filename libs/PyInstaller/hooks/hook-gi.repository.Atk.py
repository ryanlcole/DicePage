# 005527.python.hook-gi.repository.Atk.line1.comment -----------------------------------------------------------------------------
# 005528.python.hook-gi.repository.Atk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005529.python.hook-gi.repository.Atk.line3.comment
# 005530.python.hook-gi.repository.Atk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005531.python.hook-gi.repository.Atk.line5.comment or later) with exception for distributing the bootloader.
# 005532.python.hook-gi.repository.Atk.line6.comment
# 005533.python.hook-gi.repository.Atk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005534.python.hook-gi.repository.Atk.line8.comment
# 005535.python.hook-gi.repository.Atk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005536.python.hook-gi.repository.Atk.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import get_hook_config
from PyInstaller.utils.hooks.gi import GiModuleInfo, collect_glib_translations


def hook(hook_api):
    module_info = GiModuleInfo('Atk', '1.0')
    if not module_info.available:
        return

    binaries, datas, hiddenimports = module_info.collect_typelib_data()

    # 005537.python.hook-gi.repository.Atk.line23.comment Collect translations
    lang_list = get_hook_config(hook_api, "gi", "languages")
    datas += collect_glib_translations('atk10', lang_list)

    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
