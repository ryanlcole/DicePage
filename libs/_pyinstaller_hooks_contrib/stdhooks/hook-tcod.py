# 017388.python.hook-tcod.line1.comment ------------------------------------------------------------------
# 017389.python.hook-tcod.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017390.python.hook-tcod.line3.comment
# 017391.python.hook-tcod.line4.comment This file is distributed under the terms of the GNU General Public
# 017392.python.hook-tcod.line5.comment License (version 2.0 or later).
# 017393.python.hook-tcod.line6.comment
# 017394.python.hook-tcod.line7.comment The full license is available in LICENSE, distributed with
# 017395.python.hook-tcod.line8.comment this software.
# 017396.python.hook-tcod.line9.comment
# 017397.python.hook-tcod.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017398.python.hook-tcod.line11.comment ------------------------------------------------------------------
"""
Hook for https://github.com/libtcod/python-tcod
"""
from PyInstaller.utils.hooks import collect_dynamic_libs

hiddenimports = ['_cffi_backend']

# 017399.python.hook-tcod.line19.comment Install shared libraries to the working directory.
binaries = collect_dynamic_libs('tcod', destdir='.')
