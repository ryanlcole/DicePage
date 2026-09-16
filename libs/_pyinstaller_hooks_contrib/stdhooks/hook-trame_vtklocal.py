# 018041.python.hook-trame_vtklocal.line1.comment ------------------------------------------------------------------
# 018042.python.hook-trame_vtklocal.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018043.python.hook-trame_vtklocal.line3.comment
# 018044.python.hook-trame_vtklocal.line4.comment This file is distributed under the terms of the GNU General Public
# 018045.python.hook-trame_vtklocal.line5.comment License (version 2.0 or later).
# 018046.python.hook-trame_vtklocal.line6.comment
# 018047.python.hook-trame_vtklocal.line7.comment The full license is available in LICENSE, distributed with
# 018048.python.hook-trame_vtklocal.line8.comment this software.
# 018049.python.hook-trame_vtklocal.line9.comment
# 018050.python.hook-trame_vtklocal.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018051.python.hook-trame_vtklocal.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

hiddenimports = ["vtk"]
datas = collect_data_files("trame_vtklocal", subdir="module")
