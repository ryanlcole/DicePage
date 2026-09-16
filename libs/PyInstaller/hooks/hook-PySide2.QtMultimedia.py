# 004280.python.hook-PySide2.QtMultimedia.line1.comment -----------------------------------------------------------------------------
# 004281.python.hook-PySide2.QtMultimedia.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004282.python.hook-PySide2.QtMultimedia.line3.comment
# 004283.python.hook-PySide2.QtMultimedia.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004284.python.hook-PySide2.QtMultimedia.line5.comment or later) with exception for distributing the bootloader.
# 004285.python.hook-PySide2.QtMultimedia.line6.comment
# 004286.python.hook-PySide2.QtMultimedia.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004287.python.hook-PySide2.QtMultimedia.line8.comment
# 004288.python.hook-PySide2.QtMultimedia.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004289.python.hook-PySide2.QtMultimedia.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)

# 004290.python.hook-PySide2.QtMultimedia.line16.comment Using PySide2 true_properties ("from __feature__ import true_properties") causes a hidden dependency on
# 004291.python.hook-PySide2.QtMultimedia.line17.comment QtMultimediaWidgets python module:
# 004292.python.hook-PySide2.QtMultimedia.line18.comment https://github.com/qtproject/pyside-pyside-setup/blob/5.15.2/sources/shiboken2/shibokenmodule/files.dir/shibokensupport/signature/mapping.py#L577-L586
hiddenimports += ['PySide2.QtMultimediaWidgets']
