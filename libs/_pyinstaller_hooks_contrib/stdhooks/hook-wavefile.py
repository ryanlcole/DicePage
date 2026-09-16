# 020007.python.hook-wavefile.line1.comment ------------------------------------------------------------------
# 020008.python.hook-wavefile.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020009.python.hook-wavefile.line3.comment
# 020010.python.hook-wavefile.line4.comment This file is distributed under the terms of the GNU General Public
# 020011.python.hook-wavefile.line5.comment License (version 2.0 or later).
# 020012.python.hook-wavefile.line6.comment
# 020013.python.hook-wavefile.line7.comment The full license is available in LICENSE, distributed with
# 020014.python.hook-wavefile.line8.comment this software.
# 020015.python.hook-wavefile.line9.comment
# 020016.python.hook-wavefile.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020017.python.hook-wavefile.line11.comment ------------------------------------------------------------------
"""
python-wavefile: https://github.com/vokimon/python-wavefile
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('wavefile')
