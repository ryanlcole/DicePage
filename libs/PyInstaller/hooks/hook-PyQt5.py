# 003567.python.hook-PyQt5.line1.comment -----------------------------------------------------------------------------
# 003568.python.hook-PyQt5.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 003569.python.hook-PyQt5.line3.comment
# 003570.python.hook-PyQt5.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003571.python.hook-PyQt5.line5.comment or later) with exception for distributing the bootloader.
# 003572.python.hook-PyQt5.line6.comment
# 003573.python.hook-PyQt5.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003574.python.hook-PyQt5.line8.comment
# 003575.python.hook-PyQt5.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003576.python.hook-PyQt5.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import pyqt5_library_info, ensure_single_qt_bindings_package

# 003577.python.hook-PyQt5.line14.comment Allow only one Qt bindings package to be collected in frozen application.
ensure_single_qt_bindings_package("PyQt5")

# 003578.python.hook-PyQt5.line17.comment Only proceed if PyQt5 can be imported.
if pyqt5_library_info.version is not None:
    hiddenimports = [
        # 003579.python.hook-PyQt5.line20.comment PyQt5.10 and earlier uses sip in an separate package;
        'sip',
        # 003580.python.hook-PyQt5.line22.comment PyQt5.11 and later provides SIP in a private package. Support both.
        'PyQt5.sip',
        # 003581.python.hook-PyQt5.line24.comment Imported via __import__ in PyQt5/__init__.py
        'pkgutil',
    ]

    # 003582.python.hook-PyQt5.line28.comment Collect required Qt binaries.
    binaries = pyqt5_library_info.collect_extra_binaries()
