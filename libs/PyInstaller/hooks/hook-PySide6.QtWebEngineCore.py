# 005159.python.hook-PySide6.QtWebEngineCore.line1.comment -----------------------------------------------------------------------------
# 005160.python.hook-PySide6.QtWebEngineCore.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 005161.python.hook-PySide6.QtWebEngineCore.line3.comment
# 005162.python.hook-PySide6.QtWebEngineCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005163.python.hook-PySide6.QtWebEngineCore.line5.comment or later) with exception for distributing the bootloader.
# 005164.python.hook-PySide6.QtWebEngineCore.line6.comment
# 005165.python.hook-PySide6.QtWebEngineCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005166.python.hook-PySide6.QtWebEngineCore.line8.comment
# 005167.python.hook-PySide6.QtWebEngineCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005168.python.hook-PySide6.QtWebEngineCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import \
    add_qt6_dependencies, pyside6_library_info

# 005169.python.hook-PySide6.QtWebEngineCore.line15.comment Ensure PySide6 is importable before adding info depending on it.
if pyside6_library_info.version is not None:
    # 005170.python.hook-PySide6.QtWebEngineCore.line17.comment Qt6 prior to 6.2.2 contains a bug that makes it incompatible with the way PyInstaller collects
    # 005171.python.hook-PySide6.QtWebEngineCore.line18.comment QtWebEngine shared libraries and resources. So exit here and now instead of producing a defunct build.
    if pyside6_library_info.version < [6, 2, 2]:
        raise SystemExit("ERROR: PyInstaller's QtWebEngine support requires Qt6 6.2.2 or later!")

    hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

    # 005172.python.hook-PySide6.QtWebEngineCore.line24.comment Include helper process executable, translations, and resources.
    webengine_binaries, webengine_datas = pyside6_library_info.collect_qtwebengine_files()
    binaries += webengine_binaries
    datas += webengine_datas

    hiddenimports += ['PySide6.QtPrintSupport']
