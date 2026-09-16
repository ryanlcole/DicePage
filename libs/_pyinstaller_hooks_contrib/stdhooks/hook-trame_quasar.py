# 017942.python.hook-trame_quasar.line1.comment ------------------------------------------------------------------
# 017943.python.hook-trame_quasar.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017944.python.hook-trame_quasar.line3.comment
# 017945.python.hook-trame_quasar.line4.comment This file is distributed under the terms of the GNU General Public
# 017946.python.hook-trame_quasar.line5.comment License (version 2.0 or later).
# 017947.python.hook-trame_quasar.line6.comment
# 017948.python.hook-trame_quasar.line7.comment The full license is available in LICENSE, distributed with
# 017949.python.hook-trame_quasar.line8.comment this software.
# 017950.python.hook-trame_quasar.line9.comment
# 017951.python.hook-trame_quasar.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017952.python.hook-trame_quasar.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_quasar", subdir="module")]
