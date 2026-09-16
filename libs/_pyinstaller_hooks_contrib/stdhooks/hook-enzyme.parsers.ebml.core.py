# 013159.python.hook-enzyme.parsers.ebml.core.line1.comment ------------------------------------------------------------------
# 013160.python.hook-enzyme.parsers.ebml.core.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013161.python.hook-enzyme.parsers.ebml.core.line3.comment
# 013162.python.hook-enzyme.parsers.ebml.core.line4.comment This file is distributed under the terms of the GNU General Public
# 013163.python.hook-enzyme.parsers.ebml.core.line5.comment License (version 2.0 or later).
# 013164.python.hook-enzyme.parsers.ebml.core.line6.comment
# 013165.python.hook-enzyme.parsers.ebml.core.line7.comment The full license is available in LICENSE, distributed with
# 013166.python.hook-enzyme.parsers.ebml.core.line8.comment this software.
# 013167.python.hook-enzyme.parsers.ebml.core.line9.comment
# 013168.python.hook-enzyme.parsers.ebml.core.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013169.python.hook-enzyme.parsers.ebml.core.line11.comment ------------------------------------------------------------------
"""
enzyme:
https://github.com/Diaoul/enzyme
"""

import os
from PyInstaller.utils.hooks import get_package_paths

# 013170.python.hook-enzyme.parsers.ebml.core.line20.comment get path of enzyme
ep = get_package_paths('enzyme')

# 013171.python.hook-enzyme.parsers.ebml.core.line23.comment add the data
data = os.path.join(ep[1], 'parsers', 'ebml', 'specs', 'matroska.xml')
datas = [(data, "enzyme/parsers/ebml/specs")]
