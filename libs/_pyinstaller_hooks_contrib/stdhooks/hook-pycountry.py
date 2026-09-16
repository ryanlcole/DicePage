# 015511.python.hook-pycountry.line1.comment ------------------------------------------------------------------
# 015512.python.hook-pycountry.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015513.python.hook-pycountry.line3.comment
# 015514.python.hook-pycountry.line4.comment This file is distributed under the terms of the GNU General Public
# 015515.python.hook-pycountry.line5.comment License (version 2.0 or later).
# 015516.python.hook-pycountry.line6.comment
# 015517.python.hook-pycountry.line7.comment The full license is available in LICENSE, distributed with
# 015518.python.hook-pycountry.line8.comment this software.
# 015519.python.hook-pycountry.line9.comment
# 015520.python.hook-pycountry.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015521.python.hook-pycountry.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# 015522.python.hook-pycountry.line15.comment pycountry requires the ISO databases for country data.
# 015523.python.hook-pycountry.line16.comment Tested v1.15 on Linux/Ubuntu.
# 015524.python.hook-pycountry.line17.comment https://pypi.python.org/pypi/pycountry
datas = copy_metadata('pycountry') + collect_data_files('pycountry')
