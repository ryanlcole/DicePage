# 013444.python.hook-flirpy.line1.comment ------------------------------------------------------------------
# 013445.python.hook-flirpy.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 013446.python.hook-flirpy.line3.comment
# 013447.python.hook-flirpy.line4.comment This file is distributed under the terms of the GNU General Public
# 013448.python.hook-flirpy.line5.comment License (version 2.0 or later).
# 013449.python.hook-flirpy.line6.comment
# 013450.python.hook-flirpy.line7.comment The full license is available in LICENSE, distributed with
# 013451.python.hook-flirpy.line8.comment this software.
# 013452.python.hook-flirpy.line9.comment
# 013453.python.hook-flirpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013454.python.hook-flirpy.line11.comment ------------------------------------------------------------------
"""
Hook for flirpy, a library to interact with FLIR thermal imaging cameras and images.
https://github.com/LJMUAstroEcology/flirpy
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('flirpy')
