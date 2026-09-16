# 005279.python.hook-_tkinter.line1.comment -----------------------------------------------------------------------------
# 005280.python.hook-_tkinter.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005281.python.hook-_tkinter.line3.comment
# 005282.python.hook-_tkinter.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005283.python.hook-_tkinter.line5.comment or later) with exception for distributing the bootloader.
# 005284.python.hook-_tkinter.line6.comment
# 005285.python.hook-_tkinter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005286.python.hook-_tkinter.line8.comment
# 005287.python.hook-_tkinter.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005288.python.hook-_tkinter.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.tcl_tk import tcltk_info


def hook(hook_api):
    # 005289.python.hook-_tkinter.line16.comment Add all Tcl/Tk data files, based on the `TclTkInfo.data_files`. If Tcl/Tk is unavailable, the list is empty.
    # 005290.python.hook-_tkinter.line17.comment
    # 005291.python.hook-_tkinter.line18.comment NOTE: the list contains 3-element TOC tuples with full destination filenames (because other parts of code,
    # 005292.python.hook-_tkinter.line19.comment specifically splash-screen writer, currently require this format). Therefore, we need to use
    # 005293.python.hook-_tkinter.line20.comment `PostGraphAPI.add_datas` (which supports 3-element TOC tuples); if this was 2-element "hook-style" TOC list,
    # 005294.python.hook-_tkinter.line21.comment we could just assign `datas` global hook variable, without implementing the post-graph `hook()` function.
    hook_api.add_datas(tcltk_info.data_files)
