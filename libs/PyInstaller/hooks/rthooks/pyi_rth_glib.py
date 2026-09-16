# 008209.python.pyi_rth_glib.line1.comment -----------------------------------------------------------------------------
# 008210.python.pyi_rth_glib.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 008211.python.pyi_rth_glib.line3.comment
# 008212.python.pyi_rth_glib.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008213.python.pyi_rth_glib.line5.comment you may not use this file except in compliance with the License.
# 008214.python.pyi_rth_glib.line6.comment
# 008215.python.pyi_rth_glib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008216.python.pyi_rth_glib.line8.comment
# 008217.python.pyi_rth_glib.line9.comment SPDX-License-Identifier: Apache-2.0
# 008218.python.pyi_rth_glib.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    # 008219.python.pyi_rth_glib.line17.comment Prepend the frozen application's data dir to XDG_DATA_DIRS. We need to avoid overwriting the existing paths in
    # 008220.python.pyi_rth_glib.line18.comment order to allow the frozen application to run system-installed applications (for example, launch a web browser via
    # 008221.python.pyi_rth_glib.line19.comment the webbrowser module on Linux). Should the user desire complete isolation of the frozen application from the
    # 008222.python.pyi_rth_glib.line20.comment system, they need to clean up XDG_DATA_DIRS at the start of their program (i.e., remove all entries but first).
    pyi_data_dir = os.path.join(sys._MEIPASS, 'share')

    xdg_data_dirs = os.environ.get('XDG_DATA_DIRS', None)
    if xdg_data_dirs:
        if pyi_data_dir not in xdg_data_dirs:
            xdg_data_dirs = pyi_data_dir + os.pathsep + xdg_data_dirs
    else:
        xdg_data_dirs = pyi_data_dir
    os.environ['XDG_DATA_DIRS'] = xdg_data_dirs

    # 008223.python.pyi_rth_glib.line31.comment Cleanup aux variables
    del xdg_data_dirs
    del pyi_data_dir


_pyi_rthook()
del _pyi_rthook
