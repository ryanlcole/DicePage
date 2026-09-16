# 007649.python.hook-gi.repository.GstTag.line1.comment -----------------------------------------------------------------------------
# 007650.python.hook-gi.repository.GstTag.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007651.python.hook-gi.repository.GstTag.line3.comment
# 007652.python.hook-gi.repository.GstTag.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007653.python.hook-gi.repository.GstTag.line5.comment or later) with exception for distributing the bootloader.
# 007654.python.hook-gi.repository.GstTag.line6.comment
# 007655.python.hook-gi.repository.GstTag.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007656.python.hook-gi.repository.GstTag.line8.comment
# 007657.python.hook-gi.repository.GstTag.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007658.python.hook-gi.repository.GstTag.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007659.python.hook-gi.repository.GstTag.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007660.python.hook-gi.repository.GstTag.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
