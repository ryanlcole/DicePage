# 014636.python.hook-moviepy.audio.fx.all.line1.comment ------------------------------------------------------------------
# 014637.python.hook-moviepy.audio.fx.all.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014638.python.hook-moviepy.audio.fx.all.line3.comment
# 014639.python.hook-moviepy.audio.fx.all.line4.comment This file is distributed under the terms of the GNU General Public
# 014640.python.hook-moviepy.audio.fx.all.line5.comment License (version 2.0 or later).
# 014641.python.hook-moviepy.audio.fx.all.line6.comment
# 014642.python.hook-moviepy.audio.fx.all.line7.comment The full license is available in LICENSE, distributed with
# 014643.python.hook-moviepy.audio.fx.all.line8.comment this software.
# 014644.python.hook-moviepy.audio.fx.all.line9.comment
# 014645.python.hook-moviepy.audio.fx.all.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014646.python.hook-moviepy.audio.fx.all.line11.comment ------------------------------------------------------------------

# 014647.python.hook-moviepy.audio.fx.all.line13.comment `moviepy.audio.fx.all` programmatically imports and forwards all submodules of `moviepy.audio.fx`, so we need to
# 014648.python.hook-moviepy.audio.fx.all.line14.comment collect those as hidden imports.
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('moviepy.audio.fx')
