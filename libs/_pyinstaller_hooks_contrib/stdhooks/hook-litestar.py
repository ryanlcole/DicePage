# 014368.python.hook-litestar.line1.comment ------------------------------------------------------------------
# 014369.python.hook-litestar.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014370.python.hook-litestar.line3.comment
# 014371.python.hook-litestar.line4.comment This file is distributed under the terms of the GNU General Public
# 014372.python.hook-litestar.line5.comment License (version 2.0 or later).
# 014373.python.hook-litestar.line6.comment
# 014374.python.hook-litestar.line7.comment The full license is available in LICENSE, distributed with
# 014375.python.hook-litestar.line8.comment this software.
# 014376.python.hook-litestar.line9.comment
# 014377.python.hook-litestar.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014378.python.hook-litestar.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('litestar.logging')
