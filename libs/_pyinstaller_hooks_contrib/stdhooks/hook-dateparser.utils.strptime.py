# 012896.python.hook-dateparser.utils.strptime.line1.comment ------------------------------------------------------------------
# 012897.python.hook-dateparser.utils.strptime.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012898.python.hook-dateparser.utils.strptime.line3.comment
# 012899.python.hook-dateparser.utils.strptime.line4.comment This file is distributed under the terms of the GNU General Public
# 012900.python.hook-dateparser.utils.strptime.line5.comment License (version 2.0 or later).
# 012901.python.hook-dateparser.utils.strptime.line6.comment
# 012902.python.hook-dateparser.utils.strptime.line7.comment The full license is available in LICENSE, distributed with
# 012903.python.hook-dateparser.utils.strptime.line8.comment this software.
# 012904.python.hook-dateparser.utils.strptime.line9.comment
# 012905.python.hook-dateparser.utils.strptime.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012906.python.hook-dateparser.utils.strptime.line11.comment ------------------------------------------------------------------

# 012907.python.hook-dateparser.utils.strptime.line13.comment Hook for dateparser: https://pypi.org/project/dateparser/

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ["_strptime"] + collect_submodules('dateparser.data')
