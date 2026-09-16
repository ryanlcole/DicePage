# 016013.python.hook-pynput.line1.comment ------------------------------------------------------------------
# 016014.python.hook-pynput.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016015.python.hook-pynput.line3.comment
# 016016.python.hook-pynput.line4.comment This file is distributed under the terms of the GNU General Public
# 016017.python.hook-pynput.line5.comment License (version 2.0 or later).
# 016018.python.hook-pynput.line6.comment
# 016019.python.hook-pynput.line7.comment The full license is available in LICENSE, distributed with
# 016020.python.hook-pynput.line8.comment this software.
# 016021.python.hook-pynput.line9.comment
# 016022.python.hook-pynput.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016023.python.hook-pynput.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("pynput")
