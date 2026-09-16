# 018019.python.hook-trame_vtk.line1.comment ------------------------------------------------------------------
# 018020.python.hook-trame_vtk.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018021.python.hook-trame_vtk.line3.comment
# 018022.python.hook-trame_vtk.line4.comment This file is distributed under the terms of the GNU General Public
# 018023.python.hook-trame_vtk.line5.comment License (version 2.0 or later).
# 018024.python.hook-trame_vtk.line6.comment
# 018025.python.hook-trame_vtk.line7.comment The full license is available in LICENSE, distributed with
# 018026.python.hook-trame_vtk.line8.comment this software.
# 018027.python.hook-trame_vtk.line9.comment
# 018028.python.hook-trame_vtk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018029.python.hook-trame_vtk.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [
    *collect_data_files("trame_vtk", subdir="modules"),
    *collect_data_files("trame_vtk", subdir="tools"),
]
