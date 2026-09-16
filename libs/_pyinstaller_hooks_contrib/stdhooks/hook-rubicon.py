# 016549.python.hook-rubicon.line1.comment ------------------------------------------------------------------
# 016550.python.hook-rubicon.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 016551.python.hook-rubicon.line3.comment
# 016552.python.hook-rubicon.line4.comment This file is distributed under the terms of the GNU General Public
# 016553.python.hook-rubicon.line5.comment License (version 2.0 or later).
# 016554.python.hook-rubicon.line6.comment
# 016555.python.hook-rubicon.line7.comment The full license is available in LICENSE, distributed with
# 016556.python.hook-rubicon.line8.comment this software.
# 016557.python.hook-rubicon.line9.comment
# 016558.python.hook-rubicon.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016559.python.hook-rubicon.line11.comment ------------------------------------------------------------------

# 016560.python.hook-rubicon.line13.comment Prevent this package from pulling `setuptools_scm` into frozen application, as it makes no sense in that context.
excludedimports = ["setuptools_scm"]
