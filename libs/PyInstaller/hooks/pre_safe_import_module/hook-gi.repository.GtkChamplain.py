# 007745.python.hook-gi.repository.GtkChamplain.line1.comment -----------------------------------------------------------------------------
# 007746.python.hook-gi.repository.GtkChamplain.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007747.python.hook-gi.repository.GtkChamplain.line3.comment
# 007748.python.hook-gi.repository.GtkChamplain.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007749.python.hook-gi.repository.GtkChamplain.line5.comment or later) with exception for distributing the bootloader.
# 007750.python.hook-gi.repository.GtkChamplain.line6.comment
# 007751.python.hook-gi.repository.GtkChamplain.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007752.python.hook-gi.repository.GtkChamplain.line8.comment
# 007753.python.hook-gi.repository.GtkChamplain.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007754.python.hook-gi.repository.GtkChamplain.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007755.python.hook-gi.repository.GtkChamplain.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007756.python.hook-gi.repository.GtkChamplain.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
