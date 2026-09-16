# 017162.python.hook-sound_lib.line1.comment ------------------------------------------------------------------
# 017163.python.hook-sound_lib.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017164.python.hook-sound_lib.line3.comment
# 017165.python.hook-sound_lib.line4.comment This file is distributed under the terms of the GNU General Public
# 017166.python.hook-sound_lib.line5.comment License (version 2.0 or later).
# 017167.python.hook-sound_lib.line6.comment
# 017168.python.hook-sound_lib.line7.comment The full license is available in LICENSE, distributed with
# 017169.python.hook-sound_lib.line8.comment this software.
# 017170.python.hook-sound_lib.line9.comment
# 017171.python.hook-sound_lib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017172.python.hook-sound_lib.line11.comment ------------------------------------------------------------------
"""
sound_lib: http://hg.q-continuum.net/sound_lib
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('sound_lib')
