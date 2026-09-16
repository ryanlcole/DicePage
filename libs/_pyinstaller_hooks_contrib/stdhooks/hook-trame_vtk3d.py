# 018030.python.hook-trame_vtk3d.line1.comment ------------------------------------------------------------------
# 018031.python.hook-trame_vtk3d.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018032.python.hook-trame_vtk3d.line3.comment
# 018033.python.hook-trame_vtk3d.line4.comment This file is distributed under the terms of the GNU General Public
# 018034.python.hook-trame_vtk3d.line5.comment License (version 2.0 or later).
# 018035.python.hook-trame_vtk3d.line6.comment
# 018036.python.hook-trame_vtk3d.line7.comment The full license is available in LICENSE, distributed with
# 018037.python.hook-trame_vtk3d.line8.comment this software.
# 018038.python.hook-trame_vtk3d.line9.comment
# 018039.python.hook-trame_vtk3d.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018040.python.hook-trame_vtk3d.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_vtk3d", subdir="module")
