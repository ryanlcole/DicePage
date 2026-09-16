# 020296.python.hook-zeep.line1.comment ------------------------------------------------------------------
# 020297.python.hook-zeep.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020298.python.hook-zeep.line3.comment
# 020299.python.hook-zeep.line4.comment This file is distributed under the terms of the GNU General Public
# 020300.python.hook-zeep.line5.comment License (version 2.0 or later).
# 020301.python.hook-zeep.line6.comment
# 020302.python.hook-zeep.line7.comment The full license is available in LICENSE, distributed with
# 020303.python.hook-zeep.line8.comment this software.
# 020304.python.hook-zeep.line9.comment
# 020305.python.hook-zeep.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020306.python.hook-zeep.line11.comment ------------------------------------------------------------------

# 020307.python.hook-zeep.line13.comment Hook for the zeep module: https://pypi.python.org/pypi/zeep
# 020308.python.hook-zeep.line14.comment Tested with zeep 0.13.0, Python 2.7, Windows

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('zeep')
