# 007529.python.hook-gi.repository.GstInsertBin.line1.comment -----------------------------------------------------------------------------
# 007530.python.hook-gi.repository.GstInsertBin.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007531.python.hook-gi.repository.GstInsertBin.line3.comment
# 007532.python.hook-gi.repository.GstInsertBin.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007533.python.hook-gi.repository.GstInsertBin.line5.comment or later) with exception for distributing the bootloader.
# 007534.python.hook-gi.repository.GstInsertBin.line6.comment
# 007535.python.hook-gi.repository.GstInsertBin.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007536.python.hook-gi.repository.GstInsertBin.line8.comment
# 007537.python.hook-gi.repository.GstInsertBin.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007538.python.hook-gi.repository.GstInsertBin.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007539.python.hook-gi.repository.GstInsertBin.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007540.python.hook-gi.repository.GstInsertBin.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
