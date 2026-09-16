# 007397.python.hook-gi.repository.GstApp.line1.comment -----------------------------------------------------------------------------
# 007398.python.hook-gi.repository.GstApp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007399.python.hook-gi.repository.GstApp.line3.comment
# 007400.python.hook-gi.repository.GstApp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007401.python.hook-gi.repository.GstApp.line5.comment or later) with exception for distributing the bootloader.
# 007402.python.hook-gi.repository.GstApp.line6.comment
# 007403.python.hook-gi.repository.GstApp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007404.python.hook-gi.repository.GstApp.line8.comment
# 007405.python.hook-gi.repository.GstApp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007406.python.hook-gi.repository.GstApp.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007407.python.hook-gi.repository.GstApp.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007408.python.hook-gi.repository.GstApp.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
