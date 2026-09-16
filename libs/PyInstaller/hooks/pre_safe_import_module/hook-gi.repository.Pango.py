# 007817.python.hook-gi.repository.Pango.line1.comment -----------------------------------------------------------------------------
# 007818.python.hook-gi.repository.Pango.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007819.python.hook-gi.repository.Pango.line3.comment
# 007820.python.hook-gi.repository.Pango.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007821.python.hook-gi.repository.Pango.line5.comment or later) with exception for distributing the bootloader.
# 007822.python.hook-gi.repository.Pango.line6.comment
# 007823.python.hook-gi.repository.Pango.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007824.python.hook-gi.repository.Pango.line8.comment
# 007825.python.hook-gi.repository.Pango.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007826.python.hook-gi.repository.Pango.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007827.python.hook-gi.repository.Pango.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007828.python.hook-gi.repository.Pango.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
