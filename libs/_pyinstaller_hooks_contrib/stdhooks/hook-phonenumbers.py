# 015305.python.hook-phonenumbers.line1.comment ------------------------------------------------------------------
# 015306.python.hook-phonenumbers.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015307.python.hook-phonenumbers.line3.comment
# 015308.python.hook-phonenumbers.line4.comment This file is distributed under the terms of the GNU General Public
# 015309.python.hook-phonenumbers.line5.comment License (version 2.0 or later).
# 015310.python.hook-phonenumbers.line6.comment
# 015311.python.hook-phonenumbers.line7.comment The full license is available in LICENSE, distributed with
# 015312.python.hook-phonenumbers.line8.comment this software.
# 015313.python.hook-phonenumbers.line9.comment
# 015314.python.hook-phonenumbers.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015315.python.hook-phonenumbers.line11.comment ------------------------------------------------------------------
# 015316.python.hook-phonenumbers.line12.comment
# 015317.python.hook-phonenumbers.line13.comment Hook for the phonenumbers package: https://pypi.org/project/phonenumbers/
# 015318.python.hook-phonenumbers.line14.comment
# 015319.python.hook-phonenumbers.line15.comment Tested with phonenumbers 8.9.7 and Python 3.6.1, on Ubuntu 16.04 64bit.

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('phonenumbers')
