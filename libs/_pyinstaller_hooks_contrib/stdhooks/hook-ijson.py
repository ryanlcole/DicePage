# 013939.python.hook-ijson.line1.comment ------------------------------------------------------------------
# 013940.python.hook-ijson.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013941.python.hook-ijson.line3.comment
# 013942.python.hook-ijson.line4.comment This file is distributed under the terms of the GNU General Public
# 013943.python.hook-ijson.line5.comment License (version 2.0 or later).
# 013944.python.hook-ijson.line6.comment
# 013945.python.hook-ijson.line7.comment The full license is available in LICENSE, distributed with
# 013946.python.hook-ijson.line8.comment this software.
# 013947.python.hook-ijson.line9.comment
# 013948.python.hook-ijson.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013949.python.hook-ijson.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("ijson.backends")
