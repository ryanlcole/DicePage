# 007253.python.hook-gi.repository.DBus.line1.comment -----------------------------------------------------------------------------
# 007254.python.hook-gi.repository.DBus.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007255.python.hook-gi.repository.DBus.line3.comment
# 007256.python.hook-gi.repository.DBus.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007257.python.hook-gi.repository.DBus.line5.comment or later) with exception for distributing the bootloader.
# 007258.python.hook-gi.repository.DBus.line6.comment
# 007259.python.hook-gi.repository.DBus.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007260.python.hook-gi.repository.DBus.line8.comment
# 007261.python.hook-gi.repository.DBus.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007262.python.hook-gi.repository.DBus.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007263.python.hook-gi.repository.DBus.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007264.python.hook-gi.repository.DBus.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
