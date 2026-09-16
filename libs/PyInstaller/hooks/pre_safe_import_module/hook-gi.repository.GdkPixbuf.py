# 007325.python.hook-gi.repository.GdkPixbuf.line1.comment -----------------------------------------------------------------------------
# 007326.python.hook-gi.repository.GdkPixbuf.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007327.python.hook-gi.repository.GdkPixbuf.line3.comment
# 007328.python.hook-gi.repository.GdkPixbuf.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007329.python.hook-gi.repository.GdkPixbuf.line5.comment or later) with exception for distributing the bootloader.
# 007330.python.hook-gi.repository.GdkPixbuf.line6.comment
# 007331.python.hook-gi.repository.GdkPixbuf.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007332.python.hook-gi.repository.GdkPixbuf.line8.comment
# 007333.python.hook-gi.repository.GdkPixbuf.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007334.python.hook-gi.repository.GdkPixbuf.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007335.python.hook-gi.repository.GdkPixbuf.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007336.python.hook-gi.repository.GdkPixbuf.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
