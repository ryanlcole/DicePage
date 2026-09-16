# 011929.python.hook-afmformats.line1.comment ------------------------------------------------------------------
# 011930.python.hook-afmformats.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011931.python.hook-afmformats.line3.comment
# 011932.python.hook-afmformats.line4.comment This file is distributed under the terms of the GNU General Public
# 011933.python.hook-afmformats.line5.comment License (version 2.0 or later).
# 011934.python.hook-afmformats.line6.comment
# 011935.python.hook-afmformats.line7.comment The full license is available in LICENSE, distributed with
# 011936.python.hook-afmformats.line8.comment this software.
# 011937.python.hook-afmformats.line9.comment
# 011938.python.hook-afmformats.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011939.python.hook-afmformats.line11.comment ------------------------------------------------------------------

# 011940.python.hook-afmformats.line13.comment Hook for afmformats: https://pypi.python.org/pypi/afmformats

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('afmformats')
