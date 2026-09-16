# 011880.python.hook-_mysql.line1.comment ------------------------------------------------------------------
# 011881.python.hook-_mysql.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011882.python.hook-_mysql.line3.comment
# 011883.python.hook-_mysql.line4.comment This file is distributed under the terms of the GNU General Public
# 011884.python.hook-_mysql.line5.comment License (version 2.0 or later).
# 011885.python.hook-_mysql.line6.comment
# 011886.python.hook-_mysql.line7.comment The full license is available in LICENSE, distributed with
# 011887.python.hook-_mysql.line8.comment this software.
# 011888.python.hook-_mysql.line9.comment
# 011889.python.hook-_mysql.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011890.python.hook-_mysql.line11.comment ------------------------------------------------------------------
"""
Hook for _mysql, required if higher-level pure python module is not imported
"""

hiddenimports = ['_mysql_exceptions']
