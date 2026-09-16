# 007205.python.hook-gi.repository.Atk.line1.comment -----------------------------------------------------------------------------
# 007206.python.hook-gi.repository.Atk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007207.python.hook-gi.repository.Atk.line3.comment
# 007208.python.hook-gi.repository.Atk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007209.python.hook-gi.repository.Atk.line5.comment or later) with exception for distributing the bootloader.
# 007210.python.hook-gi.repository.Atk.line6.comment
# 007211.python.hook-gi.repository.Atk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007212.python.hook-gi.repository.Atk.line8.comment
# 007213.python.hook-gi.repository.Atk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007214.python.hook-gi.repository.Atk.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007215.python.hook-gi.repository.Atk.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007216.python.hook-gi.repository.Atk.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
