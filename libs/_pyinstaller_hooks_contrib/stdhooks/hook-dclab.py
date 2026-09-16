# 012931.python.hook-dclab.line1.comment ------------------------------------------------------------------
# 012932.python.hook-dclab.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012933.python.hook-dclab.line3.comment
# 012934.python.hook-dclab.line4.comment This file is distributed under the terms of the GNU General Public
# 012935.python.hook-dclab.line5.comment License (version 2.0 or later).
# 012936.python.hook-dclab.line6.comment
# 012937.python.hook-dclab.line7.comment The full license is available in LICENSE, distributed with
# 012938.python.hook-dclab.line8.comment this software.
# 012939.python.hook-dclab.line9.comment
# 012940.python.hook-dclab.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012941.python.hook-dclab.line11.comment ------------------------------------------------------------------

# 012942.python.hook-dclab.line13.comment Hook for dclab: https://pypi.python.org/pypi/dclab

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('dclab')
