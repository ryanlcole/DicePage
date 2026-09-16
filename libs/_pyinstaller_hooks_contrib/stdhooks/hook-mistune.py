# 014600.python.hook-mistune.line1.comment ------------------------------------------------------------------
# 014601.python.hook-mistune.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014602.python.hook-mistune.line3.comment
# 014603.python.hook-mistune.line4.comment This file is distributed under the terms of the GNU General Public
# 014604.python.hook-mistune.line5.comment License (version 2.0 or later).
# 014605.python.hook-mistune.line6.comment
# 014606.python.hook-mistune.line7.comment The full license is available in LICENSE, distributed with
# 014607.python.hook-mistune.line8.comment this software.
# 014608.python.hook-mistune.line9.comment
# 014609.python.hook-mistune.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014610.python.hook-mistune.line11.comment ------------------------------------------------------------------

# 014611.python.hook-mistune.line13.comment Hook for nanite: https://pypi.python.org/pypi/nanite

from PyInstaller.utils.hooks import is_module_satisfies, collect_submodules

# 014612.python.hook-mistune.line17.comment As of version 3.0.0, mistune loads its plugins indirectly (but does so during package import nevertheless).
if is_module_satisfies("mistune >= 3.0.0"):
    hiddenimports = collect_submodules("mistune.plugins")
