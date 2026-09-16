# 003024.python.hook-PIL.line1.comment -----------------------------------------------------------------------------
# 003025.python.hook-PIL.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 003026.python.hook-PIL.line3.comment
# 003027.python.hook-PIL.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003028.python.hook-PIL.line5.comment or later) with exception for distributing the bootloader.
# 003029.python.hook-PIL.line6.comment
# 003030.python.hook-PIL.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003031.python.hook-PIL.line8.comment
# 003032.python.hook-PIL.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003033.python.hook-PIL.line10.comment -----------------------------------------------------------------------------

# 003034.python.hook-PIL.line12.comment This hook was tested with Pillow 2.9.0 (Maintained fork of PIL):
# 003035.python.hook-PIL.line13.comment https://pypi.python.org/pypi/Pillow

# 003036.python.hook-PIL.line15.comment Ignore tkinter to prevent inclusion of Tcl/Tk library and other GUI libraries. Assume that if people are really using
# 003037.python.hook-PIL.line16.comment tkinter in their application, they will also import it directly and thus PyInstaller bundles the right GUI library.
excludedimports = ['tkinter', 'PyQt5', 'PySide2', 'PyQt6', 'PySide6']

# 003038.python.hook-PIL.line19.comment Similarly, prevent inclusion of IPython, which in turn ends up pulling in whole matplotlib, along with its optional
# 003039.python.hook-PIL.line20.comment GUI library dependencies.
excludedimports += ['IPython']
