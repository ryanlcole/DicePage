# 020078.python.hook-websockets.line1.comment ------------------------------------------------------------------
# 020079.python.hook-websockets.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 020080.python.hook-websockets.line3.comment
# 020081.python.hook-websockets.line4.comment This file is distributed under the terms of the GNU General Public
# 020082.python.hook-websockets.line5.comment License (version 2.0 or later).
# 020083.python.hook-websockets.line6.comment
# 020084.python.hook-websockets.line7.comment The full license is available in LICENSE, distributed with
# 020085.python.hook-websockets.line8.comment this software.
# 020086.python.hook-websockets.line9.comment
# 020087.python.hook-websockets.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020088.python.hook-websockets.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 020089.python.hook-websockets.line15.comment Websockets lazily loads its submodules.
hiddenimports = collect_submodules("websockets")
