# 007313.python.hook-gi.repository.Gdk.line1.comment -----------------------------------------------------------------------------
# 007314.python.hook-gi.repository.Gdk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007315.python.hook-gi.repository.Gdk.line3.comment
# 007316.python.hook-gi.repository.Gdk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007317.python.hook-gi.repository.Gdk.line5.comment or later) with exception for distributing the bootloader.
# 007318.python.hook-gi.repository.Gdk.line6.comment
# 007319.python.hook-gi.repository.Gdk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007320.python.hook-gi.repository.Gdk.line8.comment
# 007321.python.hook-gi.repository.Gdk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007322.python.hook-gi.repository.Gdk.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007323.python.hook-gi.repository.Gdk.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007324.python.hook-gi.repository.Gdk.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
