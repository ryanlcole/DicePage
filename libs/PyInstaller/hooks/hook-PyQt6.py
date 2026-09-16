# 004103.python.hook-PyQt6.line1.comment -----------------------------------------------------------------------------
# 004104.python.hook-PyQt6.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004105.python.hook-PyQt6.line3.comment
# 004106.python.hook-PyQt6.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004107.python.hook-PyQt6.line5.comment or later) with exception for distributing the bootloader.
# 004108.python.hook-PyQt6.line6.comment
# 004109.python.hook-PyQt6.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004110.python.hook-PyQt6.line8.comment
# 004111.python.hook-PyQt6.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004112.python.hook-PyQt6.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import pyqt6_library_info, ensure_single_qt_bindings_package

# 004113.python.hook-PyQt6.line14.comment Allow only one Qt bindings package to be collected in frozen application.
ensure_single_qt_bindings_package("PyQt6")

# 004114.python.hook-PyQt6.line17.comment Only proceed if PyQt6 can be imported.
if pyqt6_library_info.version is not None:
    hiddenimports = [
        'PyQt6.sip',
        # 004115.python.hook-PyQt6.line21.comment Imported via __import__ in PyQt6/__init__.py
        'pkgutil',
    ]

    # 004116.python.hook-PyQt6.line25.comment Collect required Qt binaries.
    binaries = pyqt6_library_info.collect_extra_binaries()
