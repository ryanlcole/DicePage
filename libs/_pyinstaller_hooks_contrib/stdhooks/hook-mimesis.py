# 014577.python.hook-mimesis.line1.comment ------------------------------------------------------------------
# 014578.python.hook-mimesis.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 014579.python.hook-mimesis.line3.comment
# 014580.python.hook-mimesis.line4.comment This file is distributed under the terms of the GNU General Public
# 014581.python.hook-mimesis.line5.comment License (version 2.0 or later).
# 014582.python.hook-mimesis.line6.comment
# 014583.python.hook-mimesis.line7.comment The full license is available in LICENSE, distributed with
# 014584.python.hook-mimesis.line8.comment this software.
# 014585.python.hook-mimesis.line9.comment
# 014586.python.hook-mimesis.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014587.python.hook-mimesis.line11.comment ------------------------------------------------------------------

# 014588.python.hook-mimesis.line13.comment The bundled 'data/' directory containing locale .json files needs to be collected (as data file).

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('mimesis')
