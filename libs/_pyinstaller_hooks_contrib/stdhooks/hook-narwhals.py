# 014727.python.hook-narwhals.line1.comment ------------------------------------------------------------------
# 014728.python.hook-narwhals.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 014729.python.hook-narwhals.line3.comment
# 014730.python.hook-narwhals.line4.comment This file is distributed under the terms of the GNU General Public
# 014731.python.hook-narwhals.line5.comment License (version 2.0 or later).
# 014732.python.hook-narwhals.line6.comment
# 014733.python.hook-narwhals.line7.comment The full license is available in LICENSE, distributed with
# 014734.python.hook-narwhals.line8.comment this software.
# 014735.python.hook-narwhals.line9.comment
# 014736.python.hook-narwhals.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014737.python.hook-narwhals.line11.comment ------------------------------------------------------------------

import sys
from PyInstaller.utils.hooks import can_import_module, copy_metadata, is_module_satisfies

# 014738.python.hook-narwhals.line16.comment Starting with narwhals 1.35.0, we need to collect metadata for `typing_extensions` if the module is available.
# 014739.python.hook-narwhals.line17.comment The codepath that checks metadata for `typing_extensions` is not executed under python >= 3.13, so we can avoid
# 014740.python.hook-narwhals.line18.comment collection there.
datas = []
if sys.version_info < (3, 13):  # PyInstaller.compat.is_py313 is available only in PyInstaller >= 6.10.0.
    if is_module_satisfies("narwhals >= 1.35.0") and can_import_module("typing_extensions"):
        datas += copy_metadata("typing_extensions")
