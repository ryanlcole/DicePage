# 007829.python.hook-gi.repository.PangoCairo.line1.comment -----------------------------------------------------------------------------
# 007830.python.hook-gi.repository.PangoCairo.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007831.python.hook-gi.repository.PangoCairo.line3.comment
# 007832.python.hook-gi.repository.PangoCairo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007833.python.hook-gi.repository.PangoCairo.line5.comment or later) with exception for distributing the bootloader.
# 007834.python.hook-gi.repository.PangoCairo.line6.comment
# 007835.python.hook-gi.repository.PangoCairo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007836.python.hook-gi.repository.PangoCairo.line8.comment
# 007837.python.hook-gi.repository.PangoCairo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007838.python.hook-gi.repository.PangoCairo.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007839.python.hook-gi.repository.PangoCairo.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007840.python.hook-gi.repository.PangoCairo.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
