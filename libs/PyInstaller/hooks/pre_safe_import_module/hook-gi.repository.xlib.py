# 007877.python.hook-gi.repository.xlib.line1.comment -----------------------------------------------------------------------------
# 007878.python.hook-gi.repository.xlib.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007879.python.hook-gi.repository.xlib.line3.comment
# 007880.python.hook-gi.repository.xlib.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007881.python.hook-gi.repository.xlib.line5.comment or later) with exception for distributing the bootloader.
# 007882.python.hook-gi.repository.xlib.line6.comment
# 007883.python.hook-gi.repository.xlib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007884.python.hook-gi.repository.xlib.line8.comment
# 007885.python.hook-gi.repository.xlib.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007886.python.hook-gi.repository.xlib.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007887.python.hook-gi.repository.xlib.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007888.python.hook-gi.repository.xlib.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
