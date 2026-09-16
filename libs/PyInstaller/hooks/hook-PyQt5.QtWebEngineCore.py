# 003465.python.hook-PyQt5.QtWebEngineCore.line1.comment -----------------------------------------------------------------------------
# 003466.python.hook-PyQt5.QtWebEngineCore.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 003467.python.hook-PyQt5.QtWebEngineCore.line3.comment
# 003468.python.hook-PyQt5.QtWebEngineCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003469.python.hook-PyQt5.QtWebEngineCore.line5.comment or later) with exception for distributing the bootloader.
# 003470.python.hook-PyQt5.QtWebEngineCore.line6.comment
# 003471.python.hook-PyQt5.QtWebEngineCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003472.python.hook-PyQt5.QtWebEngineCore.line8.comment
# 003473.python.hook-PyQt5.QtWebEngineCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003474.python.hook-PyQt5.QtWebEngineCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import \
    add_qt5_dependencies, pyqt5_library_info

# 003475.python.hook-PyQt5.QtWebEngineCore.line15.comment Ensure PyQt5 is importable before adding info depending on it.
if pyqt5_library_info.version is not None:
    hiddenimports, binaries, datas = add_qt5_dependencies(__file__)

    # 003476.python.hook-PyQt5.QtWebEngineCore.line19.comment Include helper process executable, translations, and resources.
    webengine_binaries, webengine_datas = pyqt5_library_info.collect_qtwebengine_files()
    binaries += webengine_binaries
    datas += webengine_datas
