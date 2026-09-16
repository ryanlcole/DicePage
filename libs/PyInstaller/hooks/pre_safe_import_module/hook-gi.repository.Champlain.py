# 007229.python.hook-gi.repository.Champlain.line1.comment -----------------------------------------------------------------------------
# 007230.python.hook-gi.repository.Champlain.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007231.python.hook-gi.repository.Champlain.line3.comment
# 007232.python.hook-gi.repository.Champlain.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007233.python.hook-gi.repository.Champlain.line5.comment or later) with exception for distributing the bootloader.
# 007234.python.hook-gi.repository.Champlain.line6.comment
# 007235.python.hook-gi.repository.Champlain.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007236.python.hook-gi.repository.Champlain.line8.comment
# 007237.python.hook-gi.repository.Champlain.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007238.python.hook-gi.repository.Champlain.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007239.python.hook-gi.repository.Champlain.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007240.python.hook-gi.repository.Champlain.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
