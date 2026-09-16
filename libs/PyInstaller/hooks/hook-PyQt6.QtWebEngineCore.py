# 004039.python.hook-PyQt6.QtWebEngineCore.line1.comment -----------------------------------------------------------------------------
# 004040.python.hook-PyQt6.QtWebEngineCore.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 004041.python.hook-PyQt6.QtWebEngineCore.line3.comment
# 004042.python.hook-PyQt6.QtWebEngineCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004043.python.hook-PyQt6.QtWebEngineCore.line5.comment or later) with exception for distributing the bootloader.
# 004044.python.hook-PyQt6.QtWebEngineCore.line6.comment
# 004045.python.hook-PyQt6.QtWebEngineCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004046.python.hook-PyQt6.QtWebEngineCore.line8.comment
# 004047.python.hook-PyQt6.QtWebEngineCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004048.python.hook-PyQt6.QtWebEngineCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import \
    add_qt6_dependencies, pyqt6_library_info

# 004049.python.hook-PyQt6.QtWebEngineCore.line15.comment Ensure PyQt6 is importable before adding info depending on it.
if pyqt6_library_info.version is not None:
    # 004050.python.hook-PyQt6.QtWebEngineCore.line17.comment Qt6 prior to 6.2.2 contains a bug that makes it incompatible with the way PyInstaller collects
    # 004051.python.hook-PyQt6.QtWebEngineCore.line18.comment QtWebEngine shared libraries and resources. So exit here and now instead of producing a defunct build.
    if pyqt6_library_info.version < [6, 2, 2]:
        raise SystemExit("ERROR: PyInstaller's QtWebEngine support requires Qt6 6.2.2 or later!")

    hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

    # 004052.python.hook-PyQt6.QtWebEngineCore.line24.comment Include helper process executable, translations, and resources.
    webengine_binaries, webengine_datas = pyqt6_library_info.collect_qtwebengine_files()
    binaries += webengine_binaries
    datas += webengine_datas
