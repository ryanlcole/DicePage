# 007769.python.hook-gi.repository.GtkSource.line1.comment -----------------------------------------------------------------------------
# 007770.python.hook-gi.repository.GtkSource.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007771.python.hook-gi.repository.GtkSource.line3.comment
# 007772.python.hook-gi.repository.GtkSource.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007773.python.hook-gi.repository.GtkSource.line5.comment or later) with exception for distributing the bootloader.
# 007774.python.hook-gi.repository.GtkSource.line6.comment
# 007775.python.hook-gi.repository.GtkSource.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007776.python.hook-gi.repository.GtkSource.line8.comment
# 007777.python.hook-gi.repository.GtkSource.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007778.python.hook-gi.repository.GtkSource.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007779.python.hook-gi.repository.GtkSource.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007780.python.hook-gi.repository.GtkSource.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
