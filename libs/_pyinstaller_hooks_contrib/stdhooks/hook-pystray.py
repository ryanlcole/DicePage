# 016238.python.hook-pystray.line1.comment ------------------------------------------------------------------
# 016239.python.hook-pystray.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016240.python.hook-pystray.line3.comment
# 016241.python.hook-pystray.line4.comment This file is distributed under the terms of the GNU General Public
# 016242.python.hook-pystray.line5.comment License (version 2.0 or later).
# 016243.python.hook-pystray.line6.comment
# 016244.python.hook-pystray.line7.comment The full license is available in LICENSE, distributed with
# 016245.python.hook-pystray.line8.comment this software.
# 016246.python.hook-pystray.line9.comment
# 016247.python.hook-pystray.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016248.python.hook-pystray.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules
# 016249.python.hook-pystray.line14.comment https://github.com/moses-palmer/pystray/tree/feature-explicit-backends
# 016250.python.hook-pystray.line15.comment if this get merged then we don't need this hook
hiddenimports = collect_submodules("pystray")
