# 007469.python.hook-gi.repository.GstController.line1.comment -----------------------------------------------------------------------------
# 007470.python.hook-gi.repository.GstController.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007471.python.hook-gi.repository.GstController.line3.comment
# 007472.python.hook-gi.repository.GstController.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007473.python.hook-gi.repository.GstController.line5.comment or later) with exception for distributing the bootloader.
# 007474.python.hook-gi.repository.GstController.line6.comment
# 007475.python.hook-gi.repository.GstController.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007476.python.hook-gi.repository.GstController.line8.comment
# 007477.python.hook-gi.repository.GstController.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007478.python.hook-gi.repository.GstController.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007479.python.hook-gi.repository.GstController.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007480.python.hook-gi.repository.GstController.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
