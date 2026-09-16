# 007217.python.hook-gi.repository.AyatanaAppIndicator3.line1.comment -----------------------------------------------------------------------------
# 007218.python.hook-gi.repository.AyatanaAppIndicator3.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007219.python.hook-gi.repository.AyatanaAppIndicator3.line3.comment
# 007220.python.hook-gi.repository.AyatanaAppIndicator3.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007221.python.hook-gi.repository.AyatanaAppIndicator3.line5.comment or later) with exception for distributing the bootloader.
# 007222.python.hook-gi.repository.AyatanaAppIndicator3.line6.comment
# 007223.python.hook-gi.repository.AyatanaAppIndicator3.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007224.python.hook-gi.repository.AyatanaAppIndicator3.line8.comment
# 007225.python.hook-gi.repository.AyatanaAppIndicator3.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007226.python.hook-gi.repository.AyatanaAppIndicator3.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007227.python.hook-gi.repository.AyatanaAppIndicator3.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007228.python.hook-gi.repository.AyatanaAppIndicator3.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
