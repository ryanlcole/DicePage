# 005223.python.hook-PySide6.line1.comment -----------------------------------------------------------------------------
# 005224.python.hook-PySide6.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 005225.python.hook-PySide6.line3.comment
# 005226.python.hook-PySide6.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005227.python.hook-PySide6.line5.comment or later) with exception for distributing the bootloader.
# 005228.python.hook-PySide6.line6.comment
# 005229.python.hook-PySide6.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005230.python.hook-PySide6.line8.comment
# 005231.python.hook-PySide6.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005232.python.hook-PySide6.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import check_requirement
from PyInstaller.utils.hooks.qt import pyside6_library_info, ensure_single_qt_bindings_package

# 005233.python.hook-PySide6.line15.comment Allow only one Qt bindings package to be collected in frozen application.
ensure_single_qt_bindings_package("PySide6")

# 005234.python.hook-PySide6.line18.comment Only proceed if PySide6 can be imported.
if pyside6_library_info.version is not None:
    hiddenimports = ['shiboken6', 'inspect']

    # 005235.python.hook-PySide6.line22.comment Starting with PySide6 6.4.0, we need to collect PySide6.support.deprecated for | and & operators to work with
    # 005236.python.hook-PySide6.line23.comment Qt key and key modifiers enums. See #7249.
    if check_requirement("PySide6 >= 6.4.0"):
        hiddenimports += ['PySide6.support.deprecated']

    # 005237.python.hook-PySide6.line27.comment Collect required Qt binaries.
    binaries = pyside6_library_info.collect_extra_binaries()
