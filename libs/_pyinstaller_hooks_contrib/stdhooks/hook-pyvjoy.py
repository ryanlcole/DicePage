# 016327.python.hook-pyvjoy.line1.comment ------------------------------------------------------------------
# 016328.python.hook-pyvjoy.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016329.python.hook-pyvjoy.line3.comment
# 016330.python.hook-pyvjoy.line4.comment This file is distributed under the terms of the GNU General Public
# 016331.python.hook-pyvjoy.line5.comment License (version 2.0 or later).
# 016332.python.hook-pyvjoy.line6.comment
# 016333.python.hook-pyvjoy.line7.comment The full license is available in LICENSE, distributed with
# 016334.python.hook-pyvjoy.line8.comment this software.
# 016335.python.hook-pyvjoy.line9.comment
# 016336.python.hook-pyvjoy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016337.python.hook-pyvjoy.line11.comment ------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs("pyvjoy")
