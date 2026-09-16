# 017617.python.hook-toga_gtk.line1.comment ------------------------------------------------------------------
# 017618.python.hook-toga_gtk.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017619.python.hook-toga_gtk.line3.comment
# 017620.python.hook-toga_gtk.line4.comment This file is distributed under the terms of the GNU General Public
# 017621.python.hook-toga_gtk.line5.comment License (version 2.0 or later).
# 017622.python.hook-toga_gtk.line6.comment
# 017623.python.hook-toga_gtk.line7.comment The full license is available in LICENSE, distributed with
# 017624.python.hook-toga_gtk.line8.comment this software.
# 017625.python.hook-toga_gtk.line9.comment
# 017626.python.hook-toga_gtk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017627.python.hook-toga_gtk.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# 017628.python.hook-toga_gtk.line15.comment Collect default icon from `resources`.
datas = collect_data_files('toga_gtk')

# 017629.python.hook-toga_gtk.line18.comment Collect metadata so that the backend can be discovered via `toga.backends` entry-point.
datas += copy_metadata("toga-gtk")
