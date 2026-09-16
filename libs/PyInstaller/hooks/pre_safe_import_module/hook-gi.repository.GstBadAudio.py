# 007421.python.hook-gi.repository.GstBadAudio.line1.comment -----------------------------------------------------------------------------
# 007422.python.hook-gi.repository.GstBadAudio.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007423.python.hook-gi.repository.GstBadAudio.line3.comment
# 007424.python.hook-gi.repository.GstBadAudio.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007425.python.hook-gi.repository.GstBadAudio.line5.comment or later) with exception for distributing the bootloader.
# 007426.python.hook-gi.repository.GstBadAudio.line6.comment
# 007427.python.hook-gi.repository.GstBadAudio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007428.python.hook-gi.repository.GstBadAudio.line8.comment
# 007429.python.hook-gi.repository.GstBadAudio.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007430.python.hook-gi.repository.GstBadAudio.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007431.python.hook-gi.repository.GstBadAudio.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007432.python.hook-gi.repository.GstBadAudio.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
