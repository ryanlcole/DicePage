# 018456.python.hook-vtkmodules.vtkCommonPython.line1.comment ------------------------------------------------------------------
# 018457.python.hook-vtkmodules.vtkCommonPython.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 018458.python.hook-vtkmodules.vtkCommonPython.line3.comment
# 018459.python.hook-vtkmodules.vtkCommonPython.line4.comment This file is distributed under the terms of the GNU General Public
# 018460.python.hook-vtkmodules.vtkCommonPython.line5.comment License (version 2.0 or later).
# 018461.python.hook-vtkmodules.vtkCommonPython.line6.comment
# 018462.python.hook-vtkmodules.vtkCommonPython.line7.comment The full license is available in LICENSE, distributed with
# 018463.python.hook-vtkmodules.vtkCommonPython.line8.comment this software.
# 018464.python.hook-vtkmodules.vtkCommonPython.line9.comment
# 018465.python.hook-vtkmodules.vtkCommonPython.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018466.python.hook-vtkmodules.vtkCommonPython.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.vtkmodules import add_vtkmodules_dependencies

hiddenimports = add_vtkmodules_dependencies(__file__)
