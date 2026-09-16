# 007289.python.hook-gi.repository.GModule.line1.comment -----------------------------------------------------------------------------
# 007290.python.hook-gi.repository.GModule.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007291.python.hook-gi.repository.GModule.line3.comment
# 007292.python.hook-gi.repository.GModule.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007293.python.hook-gi.repository.GModule.line5.comment or later) with exception for distributing the bootloader.
# 007294.python.hook-gi.repository.GModule.line6.comment
# 007295.python.hook-gi.repository.GModule.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007296.python.hook-gi.repository.GModule.line8.comment
# 007297.python.hook-gi.repository.GModule.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007298.python.hook-gi.repository.GModule.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007299.python.hook-gi.repository.GModule.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007300.python.hook-gi.repository.GModule.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
