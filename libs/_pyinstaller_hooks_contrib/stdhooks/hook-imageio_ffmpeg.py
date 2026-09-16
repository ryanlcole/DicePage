# 013964.python.hook-imageio_ffmpeg.line1.comment ------------------------------------------------------------------
# 013965.python.hook-imageio_ffmpeg.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013966.python.hook-imageio_ffmpeg.line3.comment
# 013967.python.hook-imageio_ffmpeg.line4.comment This file is distributed under the terms of the GNU General Public
# 013968.python.hook-imageio_ffmpeg.line5.comment License (version 2.0 or later).
# 013969.python.hook-imageio_ffmpeg.line6.comment
# 013970.python.hook-imageio_ffmpeg.line7.comment The full license is available in LICENSE, distributed with
# 013971.python.hook-imageio_ffmpeg.line8.comment this software.
# 013972.python.hook-imageio_ffmpeg.line9.comment
# 013973.python.hook-imageio_ffmpeg.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013974.python.hook-imageio_ffmpeg.line11.comment ------------------------------------------------------------------

# 013975.python.hook-imageio_ffmpeg.line13.comment Hook for imageio: http://imageio.github.io/

from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies

datas = collect_data_files('imageio_ffmpeg', subdir="binaries")

# 013976.python.hook-imageio_ffmpeg.line19.comment Starting with imageio_ffmpeg 0.5.0, `imageio_ffmpeg.binaries` is a package accessed via `importlib.resources`. Since
# 013977.python.hook-imageio_ffmpeg.line20.comment it is not directly imported anywhere, we need to add it to hidden imports.
if is_module_satisfies('imageio_ffmpeg >= 0.5.0'):
    hiddenimports = ['imageio_ffmpeg.binaries']
