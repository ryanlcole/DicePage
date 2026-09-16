# 007865.python.hook-gi.repository.freetype2.line1.comment -----------------------------------------------------------------------------
# 007866.python.hook-gi.repository.freetype2.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007867.python.hook-gi.repository.freetype2.line3.comment
# 007868.python.hook-gi.repository.freetype2.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007869.python.hook-gi.repository.freetype2.line5.comment or later) with exception for distributing the bootloader.
# 007870.python.hook-gi.repository.freetype2.line6.comment
# 007871.python.hook-gi.repository.freetype2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007872.python.hook-gi.repository.freetype2.line8.comment
# 007873.python.hook-gi.repository.freetype2.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007874.python.hook-gi.repository.freetype2.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007875.python.hook-gi.repository.freetype2.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007876.python.hook-gi.repository.freetype2.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
