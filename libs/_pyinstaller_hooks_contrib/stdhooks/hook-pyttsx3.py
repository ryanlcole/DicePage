# 016301.python.hook-pyttsx3.line1.comment ------------------------------------------------------------------
# 016302.python.hook-pyttsx3.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016303.python.hook-pyttsx3.line3.comment
# 016304.python.hook-pyttsx3.line4.comment This file is distributed under the terms of the GNU General Public
# 016305.python.hook-pyttsx3.line5.comment License (version 2.0 or later).
# 016306.python.hook-pyttsx3.line6.comment
# 016307.python.hook-pyttsx3.line7.comment The full license is available in LICENSE, distributed with
# 016308.python.hook-pyttsx3.line8.comment this software.
# 016309.python.hook-pyttsx3.line9.comment
# 016310.python.hook-pyttsx3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016311.python.hook-pyttsx3.line11.comment ------------------------------------------------------------------

# 016312.python.hook-pyttsx3.line13.comment pyttsx3 conditionally imports drivers module based on specific platform.
# 016313.python.hook-pyttsx3.line14.comment https://github.com/nateshmbhat/pyttsx3/blob/5a19376a94fdef6bfaef8795539e755b1f363fbf/pyttsx3/driver.py#L40-L50

import sys

hiddenimports = ["pyttsx3.drivers", "pyttsx3.drivers.dummy"]

# 016314.python.hook-pyttsx3.line20.comment Take directly from the link above.
if sys.platform == 'darwin':
    driverName = 'nsss'
elif sys.platform == 'win32':
    driverName = 'sapi5'
else:
    driverName = 'espeak'
# 016315.python.hook-pyttsx3.line27.comment import driver module
name = 'pyttsx3.drivers.%s' % driverName

hiddenimports.append(name)
