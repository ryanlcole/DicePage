# 015184.python.hook-pandas_flavor.line1.comment ------------------------------------------------------------------
# 015185.python.hook-pandas_flavor.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 015186.python.hook-pandas_flavor.line3.comment
# 015187.python.hook-pandas_flavor.line4.comment This file is distributed under the terms of the GNU General Public
# 015188.python.hook-pandas_flavor.line5.comment License (version 2.0 or later).
# 015189.python.hook-pandas_flavor.line6.comment
# 015190.python.hook-pandas_flavor.line7.comment The full license is available in LICENSE, distributed with
# 015191.python.hook-pandas_flavor.line8.comment this software.
# 015192.python.hook-pandas_flavor.line9.comment
# 015193.python.hook-pandas_flavor.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015194.python.hook-pandas_flavor.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 015195.python.hook-pandas_flavor.line15.comment As of version 0.3.0, pandas_flavor uses lazy loader to import `register` and `xarray` sub-modules. In earlier
# 015196.python.hook-pandas_flavor.line16.comment versions, these used to be imported directly. This was removed in 0.7.0.
if is_module_satisfies("pandas_flavor >= 0.3.0, < 0.7.0"):
    hiddenimports = ['pandas_flavor.register', 'pandas_flavor.xarray']
