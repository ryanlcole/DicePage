# 007445.python.hook-gi.repository.GstCheck.line1.comment -----------------------------------------------------------------------------
# 007446.python.hook-gi.repository.GstCheck.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007447.python.hook-gi.repository.GstCheck.line3.comment
# 007448.python.hook-gi.repository.GstCheck.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007449.python.hook-gi.repository.GstCheck.line5.comment or later) with exception for distributing the bootloader.
# 007450.python.hook-gi.repository.GstCheck.line6.comment
# 007451.python.hook-gi.repository.GstCheck.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007452.python.hook-gi.repository.GstCheck.line8.comment
# 007453.python.hook-gi.repository.GstCheck.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007454.python.hook-gi.repository.GstCheck.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007455.python.hook-gi.repository.GstCheck.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007456.python.hook-gi.repository.GstCheck.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
