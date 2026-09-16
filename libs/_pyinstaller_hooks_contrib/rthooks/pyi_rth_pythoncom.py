# 011621.python.pyi_rth_pythoncom.line1.comment -----------------------------------------------------------------------------
# 011622.python.pyi_rth_pythoncom.line2.comment Copyright (c) 2022, PyInstaller Development Team.
# 011623.python.pyi_rth_pythoncom.line3.comment
# 011624.python.pyi_rth_pythoncom.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011625.python.pyi_rth_pythoncom.line5.comment
# 011626.python.pyi_rth_pythoncom.line6.comment The full license is available in LICENSE, distributed with
# 011627.python.pyi_rth_pythoncom.line7.comment this software.
# 011628.python.pyi_rth_pythoncom.line8.comment
# 011629.python.pyi_rth_pythoncom.line9.comment SPDX-License-Identifier: Apache-2.0
# 011630.python.pyi_rth_pythoncom.line10.comment -----------------------------------------------------------------------------

# 011631.python.pyi_rth_pythoncom.line12.comment Unfortunately, __import_pywin32_system_module__ from pywintypes module assumes that in a frozen application, the
# 011632.python.pyi_rth_pythoncom.line13.comment pythoncom3X.dll and pywintypes3X.dll that are normally found in site-packages/pywin32_system32, are located
# 011633.python.pyi_rth_pythoncom.line14.comment directly in the sys.path, without bothering to check first if they are actually available in the standard location.
# 011634.python.pyi_rth_pythoncom.line15.comment This obviously runs afoul of our attempts at preserving the directory layout and placing them in the pywin32_system32
# 011635.python.pyi_rth_pythoncom.line16.comment sub-directory instead of the top-level application directory. So as a work-around, add the sub-directory to sys.path
# 011636.python.pyi_rth_pythoncom.line17.comment to keep pywintypes happy...
import sys
import os

pywin32_system32_path = os.path.join(sys._MEIPASS, 'pywin32_system32')
if os.path.isdir(pywin32_system32_path) and pywin32_system32_path not in sys.path:
    sys.path.append(pywin32_system32_path)
del pywin32_system32_path
