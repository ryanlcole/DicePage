# 018215.python.hook-unidecode.line1.comment ------------------------------------------------------------------
# 018216.python.hook-unidecode.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018217.python.hook-unidecode.line3.comment
# 018218.python.hook-unidecode.line4.comment This file is distributed under the terms of the GNU General Public
# 018219.python.hook-unidecode.line5.comment License (version 2.0 or later).
# 018220.python.hook-unidecode.line6.comment
# 018221.python.hook-unidecode.line7.comment The full license is available in LICENSE, distributed with
# 018222.python.hook-unidecode.line8.comment this software.
# 018223.python.hook-unidecode.line9.comment
# 018224.python.hook-unidecode.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018225.python.hook-unidecode.line11.comment ------------------------------------------------------------------

# 018226.python.hook-unidecode.line13.comment Hook for the unidecode package: https://pypi.python.org/pypi/unidecode
# 018227.python.hook-unidecode.line14.comment Tested with Unidecode 0.4.21 and Python 3.6.2, on Windows 10 x64.

from PyInstaller.utils.hooks import collect_submodules

# 018228.python.hook-unidecode.line18.comment Unidecode dynamically imports modules with relevant character mappings.
# 018229.python.hook-unidecode.line19.comment Non-ASCII characters are ignored if the mapping files are not found.
hiddenimports = collect_submodules('unidecode')
