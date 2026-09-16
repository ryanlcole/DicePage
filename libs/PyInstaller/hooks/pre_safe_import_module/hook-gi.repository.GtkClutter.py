# 007757.python.hook-gi.repository.GtkClutter.line1.comment -----------------------------------------------------------------------------
# 007758.python.hook-gi.repository.GtkClutter.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007759.python.hook-gi.repository.GtkClutter.line3.comment
# 007760.python.hook-gi.repository.GtkClutter.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007761.python.hook-gi.repository.GtkClutter.line5.comment or later) with exception for distributing the bootloader.
# 007762.python.hook-gi.repository.GtkClutter.line6.comment
# 007763.python.hook-gi.repository.GtkClutter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007764.python.hook-gi.repository.GtkClutter.line8.comment
# 007765.python.hook-gi.repository.GtkClutter.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007766.python.hook-gi.repository.GtkClutter.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007767.python.hook-gi.repository.GtkClutter.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007768.python.hook-gi.repository.GtkClutter.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
