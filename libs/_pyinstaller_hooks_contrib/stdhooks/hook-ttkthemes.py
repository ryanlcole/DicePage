# 018131.python.hook-ttkthemes.line1.comment ------------------------------------------------------------------
# 018132.python.hook-ttkthemes.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018133.python.hook-ttkthemes.line3.comment
# 018134.python.hook-ttkthemes.line4.comment This file is distributed under the terms of the GNU General Public
# 018135.python.hook-ttkthemes.line5.comment License (version 2.0 or later).
# 018136.python.hook-ttkthemes.line6.comment
# 018137.python.hook-ttkthemes.line7.comment The full license is available in LICENSE, distributed with
# 018138.python.hook-ttkthemes.line8.comment this software.
# 018139.python.hook-ttkthemes.line9.comment
# 018140.python.hook-ttkthemes.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018141.python.hook-ttkthemes.line11.comment ------------------------------------------------------------------
"""
Hook for use with the ttkthemes package

ttkthemes depends on a large set of image and Tcl-code files contained
within its package directory. These are not imported, and thus this hook
is required so they are copied.

The file structure of the ttkthemes package folder is:
ttkthemes
├───advanced
|   └───*.tcl
├───themes
|   ├───theme1
|   |   ├───theme1
|   |   |   └───*.gif
|   |   └───theme1.tcl
|   ├───theme2
|   ├───...
|   └───pkgIndex.tcl
├───png
└───gif

The ``themes`` directory contains themes which only have a universal
image version (either base64 encoded in the theme files or GIF), while
``png`` and ``gif`` contain the PNG and GIF versions of the themes which
support both respectively.

All of this must be copied, as the package expects all the data to be
present and only checks what themes to load at runtime.

Tested hook on Linux (Ubuntu 18.04, Python 3.6 minimal venv) and on
Windows 7 (Python 3.7, minimal system-wide installation).

>>> from tkinter import ttk
>>> from ttkthemes import ThemedTk
>>>
>>>
>>> if __name__ == '__main__':
>>>     window = ThemedTk(theme="plastik")
>>>     ttk.Button(window, text="Quit", command=window.destroy).pack()
>>>     window.mainloop()
"""
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("ttkthemes")
