# 020224.python.hook-xmlschema.line1.comment ------------------------------------------------------------------
# 020225.python.hook-xmlschema.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 020226.python.hook-xmlschema.line3.comment
# 020227.python.hook-xmlschema.line4.comment This file is distributed under the terms of the GNU General Public
# 020228.python.hook-xmlschema.line5.comment License (version 2.0 or later).
# 020229.python.hook-xmlschema.line6.comment
# 020230.python.hook-xmlschema.line7.comment The full license is available in LICENSE, distributed with
# 020231.python.hook-xmlschema.line8.comment this software.
# 020232.python.hook-xmlschema.line9.comment
# 020233.python.hook-xmlschema.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020234.python.hook-xmlschema.line11.comment ------------------------------------------------------------------

# 020235.python.hook-xmlschema.line13.comment hook for https://github.com/sissaschool/xmlschema
from PyInstaller.utils.hooks import collect_data_files

# 020236.python.hook-xmlschema.line16.comment the library contains a bunch of XSD schemas which are loaded in run time
datas = collect_data_files("xmlschema")
