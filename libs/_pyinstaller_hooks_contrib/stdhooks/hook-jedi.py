# 014041.python.hook-jedi.line1.comment ------------------------------------------------------------------
# 014042.python.hook-jedi.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014043.python.hook-jedi.line3.comment
# 014044.python.hook-jedi.line4.comment This file is distributed under the terms of the GNU General Public
# 014045.python.hook-jedi.line5.comment License (version 2.0 or later).
# 014046.python.hook-jedi.line6.comment
# 014047.python.hook-jedi.line7.comment The full license is available in LICENSE, distributed with
# 014048.python.hook-jedi.line8.comment this software.
# 014049.python.hook-jedi.line9.comment
# 014050.python.hook-jedi.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014051.python.hook-jedi.line11.comment ------------------------------------------------------------------

# 014052.python.hook-jedi.line13.comment Hook for Jedi, a static analysis tool https://pypi.org/project/jedi/

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('jedi')
