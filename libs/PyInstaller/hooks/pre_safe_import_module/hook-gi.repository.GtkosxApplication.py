# 007781.python.hook-gi.repository.GtkosxApplication.line1.comment -----------------------------------------------------------------------------
# 007782.python.hook-gi.repository.GtkosxApplication.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007783.python.hook-gi.repository.GtkosxApplication.line3.comment
# 007784.python.hook-gi.repository.GtkosxApplication.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007785.python.hook-gi.repository.GtkosxApplication.line5.comment or later) with exception for distributing the bootloader.
# 007786.python.hook-gi.repository.GtkosxApplication.line6.comment
# 007787.python.hook-gi.repository.GtkosxApplication.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007788.python.hook-gi.repository.GtkosxApplication.line8.comment
# 007789.python.hook-gi.repository.GtkosxApplication.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007790.python.hook-gi.repository.GtkosxApplication.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007791.python.hook-gi.repository.GtkosxApplication.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007792.python.hook-gi.repository.GtkosxApplication.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
