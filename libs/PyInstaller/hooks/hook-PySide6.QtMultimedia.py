# 004856.python.hook-PySide6.QtMultimedia.line1.comment -----------------------------------------------------------------------------
# 004857.python.hook-PySide6.QtMultimedia.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004858.python.hook-PySide6.QtMultimedia.line3.comment
# 004859.python.hook-PySide6.QtMultimedia.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004860.python.hook-PySide6.QtMultimedia.line5.comment or later) with exception for distributing the bootloader.
# 004861.python.hook-PySide6.QtMultimedia.line6.comment
# 004862.python.hook-PySide6.QtMultimedia.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004863.python.hook-PySide6.QtMultimedia.line8.comment
# 004864.python.hook-PySide6.QtMultimedia.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004865.python.hook-PySide6.QtMultimedia.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 004866.python.hook-PySide6.QtMultimedia.line16.comment Using PySide6 true_properties ("from __feature__ import true_properties") causes a hidden dependency on
# 004867.python.hook-PySide6.QtMultimedia.line17.comment QtMultimediaWidgets python module:
# 004868.python.hook-PySide6.QtMultimedia.line18.comment https://github.com/qtproject/pyside-pyside-setup/blob/v6.2.2.1/sources/shiboken6/shibokenmodule/files.dir/shibokensupport/signature/mapping.py#L614-L627
hiddenimports += ['PySide6.QtMultimediaWidgets']
