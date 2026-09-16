# 007793.python.hook-gi.repository.HarfBuzz.line1.comment -----------------------------------------------------------------------------
# 007794.python.hook-gi.repository.HarfBuzz.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007795.python.hook-gi.repository.HarfBuzz.line3.comment
# 007796.python.hook-gi.repository.HarfBuzz.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007797.python.hook-gi.repository.HarfBuzz.line5.comment or later) with exception for distributing the bootloader.
# 007798.python.hook-gi.repository.HarfBuzz.line6.comment
# 007799.python.hook-gi.repository.HarfBuzz.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007800.python.hook-gi.repository.HarfBuzz.line8.comment
# 007801.python.hook-gi.repository.HarfBuzz.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007802.python.hook-gi.repository.HarfBuzz.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007803.python.hook-gi.repository.HarfBuzz.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007804.python.hook-gi.repository.HarfBuzz.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
