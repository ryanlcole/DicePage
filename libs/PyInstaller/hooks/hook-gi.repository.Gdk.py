# 005622.python.hook-gi.repository.Gdk.line1.comment -----------------------------------------------------------------------------
# 005623.python.hook-gi.repository.Gdk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005624.python.hook-gi.repository.Gdk.line3.comment
# 005625.python.hook-gi.repository.Gdk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005626.python.hook-gi.repository.Gdk.line5.comment or later) with exception for distributing the bootloader.
# 005627.python.hook-gi.repository.Gdk.line6.comment
# 005628.python.hook-gi.repository.Gdk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005629.python.hook-gi.repository.Gdk.line8.comment
# 005630.python.hook-gi.repository.Gdk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005631.python.hook-gi.repository.Gdk.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo
from PyInstaller.utils.hooks import get_hook_config


def hook(hook_api):
    # 005632.python.hook-gi.repository.Gdk.line17.comment Use the Gdk version from hook config, if available. If not, try using Gtk version from hook config, so that we
    # 005633.python.hook-gi.repository.Gdk.line18.comment collect Gdk and Gtk of the same version.
    module_versions = get_hook_config(hook_api, 'gi', 'module-versions')
    if module_versions:
        version = module_versions.get('Gdk')
        if not version:
            version = module_versions.get('Gtk', '3.0')
    else:
        version = '3.0'

    module_info = GiModuleInfo('Gdk', version)
    if not module_info.available:
        return

    binaries, datas, hiddenimports = module_info.collect_typelib_data()
    hiddenimports += ['gi._gi_cairo', 'gi.repository.cairo']

    hook_api.add_datas(datas)
    hook_api.add_binaries(binaries)
    hook_api.add_imports(*hiddenimports)
