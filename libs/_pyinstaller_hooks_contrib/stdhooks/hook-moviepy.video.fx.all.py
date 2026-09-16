# 014649.python.hook-moviepy.video.fx.all.line1.comment ------------------------------------------------------------------
# 014650.python.hook-moviepy.video.fx.all.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014651.python.hook-moviepy.video.fx.all.line3.comment
# 014652.python.hook-moviepy.video.fx.all.line4.comment This file is distributed under the terms of the GNU General Public
# 014653.python.hook-moviepy.video.fx.all.line5.comment License (version 2.0 or later).
# 014654.python.hook-moviepy.video.fx.all.line6.comment
# 014655.python.hook-moviepy.video.fx.all.line7.comment The full license is available in LICENSE, distributed with
# 014656.python.hook-moviepy.video.fx.all.line8.comment this software.
# 014657.python.hook-moviepy.video.fx.all.line9.comment
# 014658.python.hook-moviepy.video.fx.all.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014659.python.hook-moviepy.video.fx.all.line11.comment ------------------------------------------------------------------

# 014660.python.hook-moviepy.video.fx.all.line13.comment `moviepy.video.fx.all` programmatically imports and forwards all submodules of `moviepy.video.fx`, so we need to
# 014661.python.hook-moviepy.video.fx.all.line14.comment collect those as hidden imports.
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('moviepy.video.fx')
