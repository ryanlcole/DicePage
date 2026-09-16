# 003012.python.hook-PIL.SpiderImagePlugin.line1.comment -----------------------------------------------------------------------------
# 003013.python.hook-PIL.SpiderImagePlugin.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 003014.python.hook-PIL.SpiderImagePlugin.line3.comment
# 003015.python.hook-PIL.SpiderImagePlugin.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003016.python.hook-PIL.SpiderImagePlugin.line5.comment or later) with exception for distributing the bootloader.
# 003017.python.hook-PIL.SpiderImagePlugin.line6.comment
# 003018.python.hook-PIL.SpiderImagePlugin.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003019.python.hook-PIL.SpiderImagePlugin.line8.comment
# 003020.python.hook-PIL.SpiderImagePlugin.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003021.python.hook-PIL.SpiderImagePlugin.line10.comment -----------------------------------------------------------------------------

# 003022.python.hook-PIL.SpiderImagePlugin.line12.comment PIL's SpiderImagePlugin features a tkPhotoImage() method, which imports ImageTk (and thus brings in the whole Tcl/Tk
# 003023.python.hook-PIL.SpiderImagePlugin.line13.comment library). Assume that if people are really using tkinter in their application, they will also import it directly.
excludedimports = ['tkinter']
