# 016039.python.hook-pyopencl.line1.comment ------------------------------------------------------------------
# 016040.python.hook-pyopencl.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016041.python.hook-pyopencl.line3.comment
# 016042.python.hook-pyopencl.line4.comment This file is distributed under the terms of the GNU General Public
# 016043.python.hook-pyopencl.line5.comment License (version 2.0 or later).
# 016044.python.hook-pyopencl.line6.comment
# 016045.python.hook-pyopencl.line7.comment The full license is available in LICENSE, distributed with
# 016046.python.hook-pyopencl.line8.comment this software.
# 016047.python.hook-pyopencl.line9.comment
# 016048.python.hook-pyopencl.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016049.python.hook-pyopencl.line11.comment ------------------------------------------------------------------

# 016050.python.hook-pyopencl.line13.comment Hook for the pyopencl module: https://github.com/pyopencl/pyopencl

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = copy_metadata('pyopencl')
datas += collect_data_files('pyopencl')
