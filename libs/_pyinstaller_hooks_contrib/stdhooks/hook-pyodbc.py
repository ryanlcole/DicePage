# 016024.python.hook-pyodbc.line1.comment ------------------------------------------------------------------
# 016025.python.hook-pyodbc.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016026.python.hook-pyodbc.line3.comment
# 016027.python.hook-pyodbc.line4.comment This file is distributed under the terms of the GNU General Public
# 016028.python.hook-pyodbc.line5.comment License (version 2.0 or later).
# 016029.python.hook-pyodbc.line6.comment
# 016030.python.hook-pyodbc.line7.comment The full license is available in LICENSE, distributed with
# 016031.python.hook-pyodbc.line8.comment this software.
# 016032.python.hook-pyodbc.line9.comment
# 016033.python.hook-pyodbc.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016034.python.hook-pyodbc.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import get_pyextension_imports

# 016035.python.hook-pyodbc.line15.comment It's hard to detect imports of binary Python module without importing it.
# 016036.python.hook-pyodbc.line16.comment Let's try importing that module in a subprocess.
# 016037.python.hook-pyodbc.line17.comment TODO function get_pyextension_imports() is experimental and we need
# 016038.python.hook-pyodbc.line18.comment to evaluate its usage here and its suitability for other hooks.
hiddenimports = get_pyextension_imports('pyodbc')
