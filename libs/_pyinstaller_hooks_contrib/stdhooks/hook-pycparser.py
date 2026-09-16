# 015525.python.hook-pycparser.line1.comment ------------------------------------------------------------------
# 015526.python.hook-pycparser.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015527.python.hook-pycparser.line3.comment
# 015528.python.hook-pycparser.line4.comment This file is distributed under the terms of the GNU General Public
# 015529.python.hook-pycparser.line5.comment License (version 2.0 or later).
# 015530.python.hook-pycparser.line6.comment
# 015531.python.hook-pycparser.line7.comment The full license is available in LICENSE, distributed with
# 015532.python.hook-pycparser.line8.comment this software.
# 015533.python.hook-pycparser.line9.comment
# 015534.python.hook-pycparser.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015535.python.hook-pycparser.line11.comment ------------------------------------------------------------------

# 015536.python.hook-pycparser.line13.comment pycparser needs two modules -- lextab.py and yacctab.py -- which it
# 015537.python.hook-pycparser.line14.comment generates at runtime if they cannot be imported.
# 015538.python.hook-pycparser.line15.comment
# 015539.python.hook-pycparser.line16.comment Those modules are written to the current working directory for which
# 015540.python.hook-pycparser.line17.comment the running process may not have write permissions, leading to a runtime
# 015541.python.hook-pycparser.line18.comment exception.
# 015542.python.hook-pycparser.line19.comment
# 015543.python.hook-pycparser.line20.comment This hook tells pyinstaller about those hidden imports, avoiding the
# 015544.python.hook-pycparser.line21.comment possibility of such runtime failures.

hiddenimports = ['pycparser.lextab', 'pycparser.yacctab']
