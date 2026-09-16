# 018142.python.hook-ttkwidgets.line1.comment ------------------------------------------------------------------
# 018143.python.hook-ttkwidgets.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018144.python.hook-ttkwidgets.line3.comment
# 018145.python.hook-ttkwidgets.line4.comment This file is distributed under the terms of the GNU General Public
# 018146.python.hook-ttkwidgets.line5.comment License (version 2.0 or later).
# 018147.python.hook-ttkwidgets.line6.comment
# 018148.python.hook-ttkwidgets.line7.comment The full license is available in LICENSE, distributed with
# 018149.python.hook-ttkwidgets.line8.comment this software.
# 018150.python.hook-ttkwidgets.line9.comment
# 018151.python.hook-ttkwidgets.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018152.python.hook-ttkwidgets.line11.comment ------------------------------------------------------------------
"""
Hook for use with the ttkwidgets package

ttkwidgets provides a set of cross-platform widgets for Tkinter/ttk,
some of which depend on image files in order to function properly.

These images files are all provided in the `ttkwidgets/assets` folder,
which has to be copied by PyInstaller.

This hook has been tested on Ubuntu 18.04 (Python 3.6.8 venv) and
Windows 7 (Python 3.5.4 system-wide).

>>> import tkinter as tk
>>> from ttkwidgets import CheckboxTreeview
>>>
>>> window = tk.Tk()
>>> tree = CheckboxTreeview(window)
>>> tree.insert("", tk.END, "test", text="Hello World!")
>>> tree.insert("test", tk.END, "test2", text="Hello World again!")
>>> tree.insert("test", tk.END, "test3", text="Hello World again again!")
>>> tree.pack()
>>> window.mainloop()
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("ttkwidgets")
