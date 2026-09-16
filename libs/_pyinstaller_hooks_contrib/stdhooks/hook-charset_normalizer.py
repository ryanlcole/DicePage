# 012518.python.hook-charset_normalizer.line1.comment ------------------------------------------------------------------
# 012519.python.hook-charset_normalizer.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 012520.python.hook-charset_normalizer.line3.comment
# 012521.python.hook-charset_normalizer.line4.comment This file is distributed under the terms of the GNU General Public
# 012522.python.hook-charset_normalizer.line5.comment License (version 2.0 or later).
# 012523.python.hook-charset_normalizer.line6.comment
# 012524.python.hook-charset_normalizer.line7.comment The full license is available in LICENSE, distributed with
# 012525.python.hook-charset_normalizer.line8.comment this software.
# 012526.python.hook-charset_normalizer.line9.comment
# 012527.python.hook-charset_normalizer.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012528.python.hook-charset_normalizer.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

if is_module_satisfies("charset_normalizer >= 3.0.1"):
    hiddenimports = ["charset_normalizer.md__mypyc"]
