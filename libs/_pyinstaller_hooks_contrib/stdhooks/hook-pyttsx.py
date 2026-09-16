# 016290.python.hook-pyttsx.line1.comment ------------------------------------------------------------------
# 016291.python.hook-pyttsx.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016292.python.hook-pyttsx.line3.comment
# 016293.python.hook-pyttsx.line4.comment This file is distributed under the terms of the GNU General Public
# 016294.python.hook-pyttsx.line5.comment License (version 2.0 or later).
# 016295.python.hook-pyttsx.line6.comment
# 016296.python.hook-pyttsx.line7.comment The full license is available in LICENSE, distributed with
# 016297.python.hook-pyttsx.line8.comment this software.
# 016298.python.hook-pyttsx.line9.comment
# 016299.python.hook-pyttsx.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016300.python.hook-pyttsx.line11.comment ------------------------------------------------------------------
"""
pyttsx imports drivers module based on specific platform.
Found at http://mrmekon.tumblr.com/post/5272210442/pyinstaller-and-pyttsx
"""

hiddenimports = [
    'drivers',
    'drivers.dummy',
    'drivers.espeak',
    'drivers.nsss',
    'drivers.sapi5',
]
