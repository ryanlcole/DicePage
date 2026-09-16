# 015209.python.hook-parsedatetime.line1.comment -----------------------------------------------------------------------------
# 015210.python.hook-parsedatetime.line2.comment Copyright (c) 2005-2020, PyInstaller Development Team.
# 015211.python.hook-parsedatetime.line3.comment
# 015212.python.hook-parsedatetime.line4.comment This file is distributed under the terms of the GNU General Public
# 015213.python.hook-parsedatetime.line5.comment License (version 2.0 or later).
# 015214.python.hook-parsedatetime.line6.comment
# 015215.python.hook-parsedatetime.line7.comment The full license is available in LICENSE, distributed with
# 015216.python.hook-parsedatetime.line8.comment this software.
# 015217.python.hook-parsedatetime.line9.comment
# 015218.python.hook-parsedatetime.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015219.python.hook-parsedatetime.line11.comment -----------------------------------------------------------------------------
"""
Fixes https://github.com/pyinstaller/pyinstaller/issues/4995

Modules under parsedatetime.pdt_locales.* are lazily loaded using __import__.
But they are conviniently listed in parsedatetime.pdt_locales.locales.

Tested on versions:

- 1.1.1
- 1.5
- 2.0
- 2.6 (latest)

"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("parsedatetime.pdt_locales")
