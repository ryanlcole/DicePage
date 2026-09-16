# 013893.python.hook-httplib2.line1.comment ------------------------------------------------------------------
# 013894.python.hook-httplib2.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013895.python.hook-httplib2.line3.comment
# 013896.python.hook-httplib2.line4.comment This file is distributed under the terms of the GNU General Public
# 013897.python.hook-httplib2.line5.comment License (version 2.0 or later).
# 013898.python.hook-httplib2.line6.comment
# 013899.python.hook-httplib2.line7.comment The full license is available in LICENSE, distributed with
# 013900.python.hook-httplib2.line8.comment this software.
# 013901.python.hook-httplib2.line9.comment
# 013902.python.hook-httplib2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013903.python.hook-httplib2.line11.comment ------------------------------------------------------------------

# 013904.python.hook-httplib2.line13.comment This is needed to bundle cacerts.txt that comes with httplib2 module

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('httplib2')
