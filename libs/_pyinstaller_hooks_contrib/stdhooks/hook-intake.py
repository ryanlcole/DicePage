# 013993.python.hook-intake.line1.comment ------------------------------------------------------------------
# 013994.python.hook-intake.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013995.python.hook-intake.line3.comment
# 013996.python.hook-intake.line4.comment This file is distributed under the terms of the GNU General Public
# 013997.python.hook-intake.line5.comment License (version 2.0 or later).
# 013998.python.hook-intake.line6.comment
# 013999.python.hook-intake.line7.comment The full license is available in LICENSE, distributed with
# 014000.python.hook-intake.line8.comment this software.
# 014001.python.hook-intake.line9.comment
# 014002.python.hook-intake.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014003.python.hook-intake.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_entry_point

datas, hiddenimports = collect_entry_point('intake.drivers')
