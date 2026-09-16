# 004626.python.hook-PySide2.Qwt5.line1.comment -----------------------------------------------------------------------------
# 004627.python.hook-PySide2.Qwt5.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004628.python.hook-PySide2.Qwt5.line3.comment
# 004629.python.hook-PySide2.Qwt5.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004630.python.hook-PySide2.Qwt5.line5.comment or later) with exception for distributing the bootloader.
# 004631.python.hook-PySide2.Qwt5.line6.comment
# 004632.python.hook-PySide2.Qwt5.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004633.python.hook-PySide2.Qwt5.line8.comment
# 004634.python.hook-PySide2.Qwt5.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004635.python.hook-PySide2.Qwt5.line10.comment -----------------------------------------------------------------------------

from PyInstaller import isolated

hiddenimports = ['PySide2.QtCore', 'PySide2.QtWidgets', 'PySide2.QtGui', 'PySide2.QtSvg']


@isolated.decorate
def conditional_imports():
    from PySide2 import Qwt5

    out = []
    if hasattr(Qwt5, "toNumpy"):
        out.append("numpy")
    if hasattr(Qwt5, "toNumeric"):
        out.append("numeric")
    if hasattr(Qwt5, "toNumarray"):
        out.append("numarray")
    return out


hiddenimports += conditional_imports()
