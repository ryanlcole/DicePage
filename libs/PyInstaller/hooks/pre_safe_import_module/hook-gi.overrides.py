# 007143.python.hook-gi.overrides.line1.comment -----------------------------------------------------------------------------
# 007144.python.hook-gi.overrides.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 007145.python.hook-gi.overrides.line3.comment
# 007146.python.hook-gi.overrides.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007147.python.hook-gi.overrides.line5.comment or later) with exception for distributing the bootloader.
# 007148.python.hook-gi.overrides.line6.comment
# 007149.python.hook-gi.overrides.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007150.python.hook-gi.overrides.line8.comment
# 007151.python.hook-gi.overrides.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007152.python.hook-gi.overrides.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat
from PyInstaller.utils import hooks as hookutils


def pre_safe_import_module(api):
    if compat.is_linux:
        # 007153.python.hook-gi.overrides.line18.comment See comment in the adjacent `hook-gi.py`.
        try:
            paths = hookutils.get_module_attribute(api.module_name, "__path__")
        except Exception:
            # 007154.python.hook-gi.overrides.line22.comment Most likely `gi.overrides` cannot be imported.
            paths = []

        for path in paths:
            api.append_package_path(path)
