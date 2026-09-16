# 007090.python.hook-tkinter.line1.comment -----------------------------------------------------------------------------
# 007091.python.hook-tkinter.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 007092.python.hook-tkinter.line3.comment
# 007093.python.hook-tkinter.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007094.python.hook-tkinter.line5.comment or later) with exception for distributing the bootloader.
# 007095.python.hook-tkinter.line6.comment
# 007096.python.hook-tkinter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007097.python.hook-tkinter.line8.comment
# 007098.python.hook-tkinter.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007099.python.hook-tkinter.line10.comment -----------------------------------------------------------------------------

from PyInstaller import log as logging
from PyInstaller.utils.hooks import tcl_tk

logger = logging.getLogger(__name__)


def pre_find_module_path(hook_api):
    if not tcl_tk.tcltk_info.available:
        logger.warning("tkinter installation is broken. It will be excluded from the application")
        hook_api.search_dirs = []
