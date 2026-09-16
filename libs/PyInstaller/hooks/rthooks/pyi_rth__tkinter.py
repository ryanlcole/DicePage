# 008151.python.pyi_rth__tkinter.line1.comment -----------------------------------------------------------------------------
# 008152.python.pyi_rth__tkinter.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008153.python.pyi_rth__tkinter.line3.comment
# 008154.python.pyi_rth__tkinter.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008155.python.pyi_rth__tkinter.line5.comment you may not use this file except in compliance with the License.
# 008156.python.pyi_rth__tkinter.line6.comment
# 008157.python.pyi_rth__tkinter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008158.python.pyi_rth__tkinter.line8.comment
# 008159.python.pyi_rth__tkinter.line9.comment SPDX-License-Identifier: Apache-2.0
# 008160.python.pyi_rth__tkinter.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    # 008161.python.pyi_rth__tkinter.line17.comment The directory names must match TCL_ROOTNAME and TK_ROOTNAME constants defined in `PyInstaller.utils.hooks.tcl_tk`.
    tcldir = os.path.join(sys._MEIPASS, '_tcl_data')
    tkdir = os.path.join(sys._MEIPASS, '_tk_data')

    # 008162.python.pyi_rth__tkinter.line21.comment Notify "tkinter" of data directories. On macOS, we do not collect data directories if system Tcl/Tk framework is
    # 008163.python.pyi_rth__tkinter.line22.comment used. On other OSes, we always collect them, so their absence is considered an error.
    is_darwin = sys.platform == 'darwin'

    if os.path.isdir(tcldir):
        os.environ["TCL_LIBRARY"] = tcldir
    elif not is_darwin:
        raise FileNotFoundError('Tcl data directory "%s" not found.' % tcldir)

    if os.path.isdir(tkdir):
        os.environ["TK_LIBRARY"] = tkdir
    elif not is_darwin:
        raise FileNotFoundError('Tk data directory "%s" not found.' % tkdir)


_pyi_rthook()
del _pyi_rthook
