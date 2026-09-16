# 011637.python.pyi_rth_pywintypes.line1.comment -----------------------------------------------------------------------------
# 011638.python.pyi_rth_pywintypes.line2.comment Copyright (c) 2022, PyInstaller Development Team.
# 011639.python.pyi_rth_pywintypes.line3.comment
# 011640.python.pyi_rth_pywintypes.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011641.python.pyi_rth_pywintypes.line5.comment
# 011642.python.pyi_rth_pywintypes.line6.comment The full license is available in LICENSE, distributed with
# 011643.python.pyi_rth_pywintypes.line7.comment this software.
# 011644.python.pyi_rth_pywintypes.line8.comment
# 011645.python.pyi_rth_pywintypes.line9.comment SPDX-License-Identifier: Apache-2.0
# 011646.python.pyi_rth_pywintypes.line10.comment -----------------------------------------------------------------------------

# 011647.python.pyi_rth_pywintypes.line12.comment Unfortunately, __import_pywin32_system_module__ from pywintypes module assumes that in a frozen application, the
# 011648.python.pyi_rth_pywintypes.line13.comment pythoncom3X.dll and pywintypes3X.dll that are normally found in site-packages/pywin32_system32, are located
# 011649.python.pyi_rth_pywintypes.line14.comment directly in the sys.path, without bothering to check first if they are actually available in the standard location.
# 011650.python.pyi_rth_pywintypes.line15.comment This obviously runs afoul of our attempts at preserving the directory layout and placing them in the pywin32_system32
# 011651.python.pyi_rth_pywintypes.line16.comment sub-directory instead of the top-level application directory. So as a work-around, add the sub-directory to sys.path
# 011652.python.pyi_rth_pywintypes.line17.comment to keep pywintypes happy...
import sys
import os

pywin32_system32_path = os.path.join(sys._MEIPASS, 'pywin32_system32')
if os.path.isdir(pywin32_system32_path) and pywin32_system32_path not in sys.path:
    sys.path.append(pywin32_system32_path)
del pywin32_system32_path
