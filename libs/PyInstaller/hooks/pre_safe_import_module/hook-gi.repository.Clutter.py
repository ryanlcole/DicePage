# 007241.python.hook-gi.repository.Clutter.line1.comment -----------------------------------------------------------------------------
# 007242.python.hook-gi.repository.Clutter.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007243.python.hook-gi.repository.Clutter.line3.comment
# 007244.python.hook-gi.repository.Clutter.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007245.python.hook-gi.repository.Clutter.line5.comment or later) with exception for distributing the bootloader.
# 007246.python.hook-gi.repository.Clutter.line6.comment
# 007247.python.hook-gi.repository.Clutter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007248.python.hook-gi.repository.Clutter.line8.comment
# 007249.python.hook-gi.repository.Clutter.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007250.python.hook-gi.repository.Clutter.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007251.python.hook-gi.repository.Clutter.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007252.python.hook-gi.repository.Clutter.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
