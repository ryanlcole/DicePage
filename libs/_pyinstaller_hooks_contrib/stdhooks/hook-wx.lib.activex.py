# 020139.python.hook-wx.lib.activex.line1.comment ------------------------------------------------------------------
# 020140.python.hook-wx.lib.activex.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020141.python.hook-wx.lib.activex.line3.comment
# 020142.python.hook-wx.lib.activex.line4.comment This file is distributed under the terms of the GNU General Public
# 020143.python.hook-wx.lib.activex.line5.comment License (version 2.0 or later).
# 020144.python.hook-wx.lib.activex.line6.comment
# 020145.python.hook-wx.lib.activex.line7.comment The full license is available in LICENSE, distributed with
# 020146.python.hook-wx.lib.activex.line8.comment this software.
# 020147.python.hook-wx.lib.activex.line9.comment
# 020148.python.hook-wx.lib.activex.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020149.python.hook-wx.lib.activex.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import exec_statement

# 020150.python.hook-wx.lib.activex.line15.comment This needed because comtypes wx.lib.activex generates some stuff.
exec_statement("import wx.lib.activex")
