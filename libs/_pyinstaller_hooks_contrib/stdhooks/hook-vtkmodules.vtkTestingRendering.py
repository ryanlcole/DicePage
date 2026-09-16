# 019919.python.hook-vtkmodules.vtkTestingRendering.line1.comment ------------------------------------------------------------------
# 019920.python.hook-vtkmodules.vtkTestingRendering.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 019921.python.hook-vtkmodules.vtkTestingRendering.line3.comment
# 019922.python.hook-vtkmodules.vtkTestingRendering.line4.comment This file is distributed under the terms of the GNU General Public
# 019923.python.hook-vtkmodules.vtkTestingRendering.line5.comment License (version 2.0 or later).
# 019924.python.hook-vtkmodules.vtkTestingRendering.line6.comment
# 019925.python.hook-vtkmodules.vtkTestingRendering.line7.comment The full license is available in LICENSE, distributed with
# 019926.python.hook-vtkmodules.vtkTestingRendering.line8.comment this software.
# 019927.python.hook-vtkmodules.vtkTestingRendering.line9.comment
# 019928.python.hook-vtkmodules.vtkTestingRendering.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 019929.python.hook-vtkmodules.vtkTestingRendering.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.vtkmodules import add_vtkmodules_dependencies

hiddenimports = add_vtkmodules_dependencies(__file__)
