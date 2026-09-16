# 011795.python.hook-IPython.line1.comment ------------------------------------------------------------------
# 011796.python.hook-IPython.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011797.python.hook-IPython.line3.comment
# 011798.python.hook-IPython.line4.comment This file is distributed under the terms of the GNU General Public
# 011799.python.hook-IPython.line5.comment License (version 2.0 or later).
# 011800.python.hook-IPython.line6.comment
# 011801.python.hook-IPython.line7.comment The full license is available in LICENSE, distributed with
# 011802.python.hook-IPython.line8.comment this software.
# 011803.python.hook-IPython.line9.comment
# 011804.python.hook-IPython.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011805.python.hook-IPython.line11.comment ------------------------------------------------------------------

# 011806.python.hook-IPython.line13.comment Tested with IPython 4.0.0.

from PyInstaller.compat import is_win, is_darwin
from PyInstaller.utils.hooks import collect_data_files

# 011807.python.hook-IPython.line18.comment Ignore 'matplotlib'. IPython contains support for matplotlib.
# 011808.python.hook-IPython.line19.comment Ignore GUI libraries. IPython supports integration with GUI frameworks.
# 011809.python.hook-IPython.line20.comment Assume that it will be imported by any other module when the user really
# 011810.python.hook-IPython.line21.comment uses it.
excludedimports = [
    'gtk',
    'matplotlib',
    'PySide',
    'PyQt4',
    'PySide2',
    'PyQt5',
    'PySide6',
    'PyQt6',
]

# 011811.python.hook-IPython.line33.comment IPython uses 'tkinter' for clipboard access on Linux/Unix. Exclude it on Windows and OS X.
if is_win or is_darwin:
    excludedimports.append('tkinter')

datas = collect_data_files('IPython')

# 011812.python.hook-IPython.line39.comment IPython imports extensions by changing to the extensions directory and using
# 011813.python.hook-IPython.line40.comment importlib.import_module, so we need to copy over the extensions as if they
# 011814.python.hook-IPython.line41.comment were data files.
datas += collect_data_files('IPython.extensions', include_py_files=True)
