# 018081.python.hook-travertino.line1.comment ------------------------------------------------------------------
# 018082.python.hook-travertino.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018083.python.hook-travertino.line3.comment
# 018084.python.hook-travertino.line4.comment This file is distributed under the terms of the GNU General Public
# 018085.python.hook-travertino.line5.comment License (version 2.0 or later).
# 018086.python.hook-travertino.line6.comment
# 018087.python.hook-travertino.line7.comment The full license is available in LICENSE, distributed with
# 018088.python.hook-travertino.line8.comment this software.
# 018089.python.hook-travertino.line9.comment
# 018090.python.hook-travertino.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018091.python.hook-travertino.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata

# 018092.python.hook-travertino.line15.comment Prevent this package from pulling `setuptools_scm` into frozen application, as it makes no sense in that context.
excludedimports = ["setuptools_scm"]

# 018093.python.hook-travertino.line18.comment Collect metadata to allow package to infer its version at run-time.
datas = copy_metadata("travertino")
