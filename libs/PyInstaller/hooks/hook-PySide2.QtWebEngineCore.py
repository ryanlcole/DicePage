# 004524.python.hook-PySide2.QtWebEngineCore.line1.comment -----------------------------------------------------------------------------
# 004525.python.hook-PySide2.QtWebEngineCore.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 004526.python.hook-PySide2.QtWebEngineCore.line3.comment
# 004527.python.hook-PySide2.QtWebEngineCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004528.python.hook-PySide2.QtWebEngineCore.line5.comment or later) with exception for distributing the bootloader.
# 004529.python.hook-PySide2.QtWebEngineCore.line6.comment
# 004530.python.hook-PySide2.QtWebEngineCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004531.python.hook-PySide2.QtWebEngineCore.line8.comment
# 004532.python.hook-PySide2.QtWebEngineCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004533.python.hook-PySide2.QtWebEngineCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import \
    add_qt5_dependencies, pyside2_library_info

# 004534.python.hook-PySide2.QtWebEngineCore.line15.comment Ensure PySide2 is importable before adding info depending on it.
if pyside2_library_info.version is not None:
    hiddenimports, binaries, datas = add_qt5_dependencies(__file__)

    # 004535.python.hook-PySide2.QtWebEngineCore.line19.comment Include helper process executable, translations, and resources.
    webengine_binaries, webengine_datas = pyside2_library_info.collect_qtwebengine_files()
    binaries += webengine_binaries
    datas += webengine_datas
