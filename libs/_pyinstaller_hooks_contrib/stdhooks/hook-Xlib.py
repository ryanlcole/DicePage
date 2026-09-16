# 011858.python.hook-Xlib.line1.comment ------------------------------------------------------------------
# 011859.python.hook-Xlib.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011860.python.hook-Xlib.line3.comment
# 011861.python.hook-Xlib.line4.comment This file is distributed under the terms of the GNU General Public
# 011862.python.hook-Xlib.line5.comment License (version 2.0 or later).
# 011863.python.hook-Xlib.line6.comment
# 011864.python.hook-Xlib.line7.comment The full license is available in LICENSE, distributed with
# 011865.python.hook-Xlib.line8.comment this software.
# 011866.python.hook-Xlib.line9.comment
# 011867.python.hook-Xlib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011868.python.hook-Xlib.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('Xlib')
