# 017909.python.hook-trame_mesh_streamer.line1.comment ------------------------------------------------------------------
# 017910.python.hook-trame_mesh_streamer.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017911.python.hook-trame_mesh_streamer.line3.comment
# 017912.python.hook-trame_mesh_streamer.line4.comment This file is distributed under the terms of the GNU General Public
# 017913.python.hook-trame_mesh_streamer.line5.comment License (version 2.0 or later).
# 017914.python.hook-trame_mesh_streamer.line6.comment
# 017915.python.hook-trame_mesh_streamer.line7.comment The full license is available in LICENSE, distributed with
# 017916.python.hook-trame_mesh_streamer.line8.comment this software.
# 017917.python.hook-trame_mesh_streamer.line9.comment
# 017918.python.hook-trame_mesh_streamer.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017919.python.hook-trame_mesh_streamer.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

hiddenimports = ["vtk"]
datas = collect_data_files("trame_mesh_streamer", subdir="module")
