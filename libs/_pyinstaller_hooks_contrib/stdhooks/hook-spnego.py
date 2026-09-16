# 017242.python.hook-spnego.line1.comment ------------------------------------------------------------------
# 017243.python.hook-spnego.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017244.python.hook-spnego.line3.comment
# 017245.python.hook-spnego.line4.comment This file is distributed under the terms of the GNU General Public
# 017246.python.hook-spnego.line5.comment License (version 2.0 or later).
# 017247.python.hook-spnego.line6.comment
# 017248.python.hook-spnego.line7.comment The full license is available in LICENSE, distributed with
# 017249.python.hook-spnego.line8.comment this software.
# 017250.python.hook-spnego.line9.comment
# 017251.python.hook-spnego.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017252.python.hook-spnego.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('spnego')
