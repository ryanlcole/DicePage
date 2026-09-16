# 007661.python.hook-gi.repository.GstTranscoder.line1.comment -----------------------------------------------------------------------------
# 007662.python.hook-gi.repository.GstTranscoder.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007663.python.hook-gi.repository.GstTranscoder.line3.comment
# 007664.python.hook-gi.repository.GstTranscoder.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007665.python.hook-gi.repository.GstTranscoder.line5.comment or later) with exception for distributing the bootloader.
# 007666.python.hook-gi.repository.GstTranscoder.line6.comment
# 007667.python.hook-gi.repository.GstTranscoder.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007668.python.hook-gi.repository.GstTranscoder.line8.comment
# 007669.python.hook-gi.repository.GstTranscoder.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007670.python.hook-gi.repository.GstTranscoder.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007671.python.hook-gi.repository.GstTranscoder.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007672.python.hook-gi.repository.GstTranscoder.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
