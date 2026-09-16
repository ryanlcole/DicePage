# 007589.python.hook-gi.repository.GstPlayer.line1.comment -----------------------------------------------------------------------------
# 007590.python.hook-gi.repository.GstPlayer.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007591.python.hook-gi.repository.GstPlayer.line3.comment
# 007592.python.hook-gi.repository.GstPlayer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007593.python.hook-gi.repository.GstPlayer.line5.comment or later) with exception for distributing the bootloader.
# 007594.python.hook-gi.repository.GstPlayer.line6.comment
# 007595.python.hook-gi.repository.GstPlayer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007596.python.hook-gi.repository.GstPlayer.line8.comment
# 007597.python.hook-gi.repository.GstPlayer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007598.python.hook-gi.repository.GstPlayer.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007599.python.hook-gi.repository.GstPlayer.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007600.python.hook-gi.repository.GstPlayer.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
