# 014819.python.hook-niquests.line1.comment ------------------------------------------------------------------
# 014820.python.hook-niquests.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 014821.python.hook-niquests.line3.comment
# 014822.python.hook-niquests.line4.comment This file is distributed under the terms of the GNU General Public
# 014823.python.hook-niquests.line5.comment License (version 2.0 or later).
# 014824.python.hook-niquests.line6.comment
# 014825.python.hook-niquests.line7.comment The full license is available in LICENSE, distributed with
# 014826.python.hook-niquests.line8.comment this software.
# 014827.python.hook-niquests.line9.comment
# 014828.python.hook-niquests.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014829.python.hook-niquests.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("niquests")
