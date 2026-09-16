# 007337.python.hook-gi.repository.Gio.line1.comment -----------------------------------------------------------------------------
# 007338.python.hook-gi.repository.Gio.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007339.python.hook-gi.repository.Gio.line3.comment
# 007340.python.hook-gi.repository.Gio.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007341.python.hook-gi.repository.Gio.line5.comment or later) with exception for distributing the bootloader.
# 007342.python.hook-gi.repository.Gio.line6.comment
# 007343.python.hook-gi.repository.Gio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007344.python.hook-gi.repository.Gio.line8.comment
# 007345.python.hook-gi.repository.Gio.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007346.python.hook-gi.repository.Gio.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007347.python.hook-gi.repository.Gio.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007348.python.hook-gi.repository.Gio.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
