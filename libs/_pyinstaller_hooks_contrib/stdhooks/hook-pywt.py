# 016355.python.hook-pywt.line1.comment ------------------------------------------------------------------
# 016356.python.hook-pywt.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016357.python.hook-pywt.line3.comment
# 016358.python.hook-pywt.line4.comment This file is distributed under the terms of the GNU General Public
# 016359.python.hook-pywt.line5.comment License (version 2.0 or later).
# 016360.python.hook-pywt.line6.comment
# 016361.python.hook-pywt.line7.comment The full license is available in LICENSE, distributed with
# 016362.python.hook-pywt.line8.comment this software.
# 016363.python.hook-pywt.line9.comment
# 016364.python.hook-pywt.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016365.python.hook-pywt.line11.comment ------------------------------------------------------------------

# 016366.python.hook-pywt.line13.comment Hook for https://github.com/PyWavelets/pywt

hiddenimports = ['pywt._extensions._cwt']

# 016367.python.hook-pywt.line17.comment NOTE: There is another project `https://github.com/Knapstad/pywt installing
# 016368.python.hook-pywt.line18.comment a packagre `pywt`, too. This name clash is not much of a problem, even if
# 016369.python.hook-pywt.line19.comment this hook is picked up for the other package, since PyInstaller will simply
# 016370.python.hook-pywt.line20.comment skip any module added by this hook but acutally missing. If the other project
# 016371.python.hook-pywt.line21.comment requires a hook, too, simply add it to this file.
