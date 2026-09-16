# 020212.python.hook-xmldiff.line1.comment ------------------------------------------------------------------
# 020213.python.hook-xmldiff.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020214.python.hook-xmldiff.line3.comment
# 020215.python.hook-xmldiff.line4.comment This file is distributed under the terms of the GNU General Public
# 020216.python.hook-xmldiff.line5.comment License (version 2.0 or later).
# 020217.python.hook-xmldiff.line6.comment
# 020218.python.hook-xmldiff.line7.comment The full license is available in LICENSE, distributed with
# 020219.python.hook-xmldiff.line8.comment this software.
# 020220.python.hook-xmldiff.line9.comment
# 020221.python.hook-xmldiff.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020222.python.hook-xmldiff.line11.comment ------------------------------------------------------------------
# 020223.python.hook-xmldiff.line12.comment Hook for https://github.com/Shoobx/xmldiff

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('xmldiff')
