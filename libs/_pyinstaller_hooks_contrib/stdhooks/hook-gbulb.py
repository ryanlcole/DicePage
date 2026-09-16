# 013537.python.hook-gbulb.line1.comment ------------------------------------------------------------------
# 013538.python.hook-gbulb.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 013539.python.hook-gbulb.line3.comment
# 013540.python.hook-gbulb.line4.comment This file is distributed under the terms of the GNU General Public
# 013541.python.hook-gbulb.line5.comment License (version 2.0 or later).
# 013542.python.hook-gbulb.line6.comment
# 013543.python.hook-gbulb.line7.comment The full license is available in LICENSE, distributed with
# 013544.python.hook-gbulb.line8.comment this software.
# 013545.python.hook-gbulb.line9.comment
# 013546.python.hook-gbulb.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013547.python.hook-gbulb.line11.comment ------------------------------------------------------------------

# 013548.python.hook-gbulb.line13.comment Prevent this package from pulling `setuptools_scm` into frozen application, as it makes no sense in that context.
excludedimports = ["setuptools_scm"]
