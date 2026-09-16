# 015608.python.hook-pydivert.line1.comment ------------------------------------------------------------------
# 015609.python.hook-pydivert.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015610.python.hook-pydivert.line3.comment
# 015611.python.hook-pydivert.line4.comment This file is distributed under the terms of the GNU General Public
# 015612.python.hook-pydivert.line5.comment License (version 2.0 or later).
# 015613.python.hook-pydivert.line6.comment
# 015614.python.hook-pydivert.line7.comment The full license is available in LICENSE, distributed with
# 015615.python.hook-pydivert.line8.comment this software.
# 015616.python.hook-pydivert.line9.comment
# 015617.python.hook-pydivert.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015618.python.hook-pydivert.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pydivert.windivert_dll')
