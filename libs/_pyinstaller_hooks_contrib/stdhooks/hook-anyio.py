# 011974.python.hook-anyio.line1.comment ------------------------------------------------------------------
# 011975.python.hook-anyio.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011976.python.hook-anyio.line3.comment
# 011977.python.hook-anyio.line4.comment This file is distributed under the terms of the GNU General Public
# 011978.python.hook-anyio.line5.comment License (version 2.0 or later).
# 011979.python.hook-anyio.line6.comment
# 011980.python.hook-anyio.line7.comment The full license is available in LICENSE, distributed with
# 011981.python.hook-anyio.line8.comment this software.
# 011982.python.hook-anyio.line9.comment
# 011983.python.hook-anyio.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011984.python.hook-anyio.line11.comment ------------------------------------------------------------------
"""
AnyIO contains a number of back-ends as dynamically imported modules.
This hook was tested against AnyIO v1.4.0.
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('anyio._backends')
