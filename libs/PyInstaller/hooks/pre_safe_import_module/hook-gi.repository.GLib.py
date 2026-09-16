# 007277.python.hook-gi.repository.GLib.line1.comment -----------------------------------------------------------------------------
# 007278.python.hook-gi.repository.GLib.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007279.python.hook-gi.repository.GLib.line3.comment
# 007280.python.hook-gi.repository.GLib.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007281.python.hook-gi.repository.GLib.line5.comment or later) with exception for distributing the bootloader.
# 007282.python.hook-gi.repository.GLib.line6.comment
# 007283.python.hook-gi.repository.GLib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007284.python.hook-gi.repository.GLib.line8.comment
# 007285.python.hook-gi.repository.GLib.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007286.python.hook-gi.repository.GLib.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007287.python.hook-gi.repository.GLib.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007288.python.hook-gi.repository.GLib.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
