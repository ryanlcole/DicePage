# 012919.python.hook-dbus_fast.line1.comment ------------------------------------------------------------------
# 012920.python.hook-dbus_fast.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 012921.python.hook-dbus_fast.line3.comment
# 012922.python.hook-dbus_fast.line4.comment This file is distributed under the terms of the GNU General Public
# 012923.python.hook-dbus_fast.line5.comment License (version 2.0 or later).
# 012924.python.hook-dbus_fast.line6.comment
# 012925.python.hook-dbus_fast.line7.comment The full license is available in LICENSE, distributed with
# 012926.python.hook-dbus_fast.line8.comment this software.
# 012927.python.hook-dbus_fast.line9.comment
# 012928.python.hook-dbus_fast.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012929.python.hook-dbus_fast.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 012930.python.hook-dbus_fast.line15.comment Collect all submodules to handle imports made from cythonized extensions.
hiddenimports = collect_submodules('dbus_fast')
