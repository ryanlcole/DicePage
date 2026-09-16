# 013385.python.hook-ffpyplayer.line1.comment ------------------------------------------------------------------
# 013386.python.hook-ffpyplayer.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 013387.python.hook-ffpyplayer.line3.comment
# 013388.python.hook-ffpyplayer.line4.comment This file is distributed under the terms of the GNU General Public
# 013389.python.hook-ffpyplayer.line5.comment License (version 2.0 or later).
# 013390.python.hook-ffpyplayer.line6.comment
# 013391.python.hook-ffpyplayer.line7.comment The full license is available in LICENSE, distributed with
# 013392.python.hook-ffpyplayer.line8.comment this software.
# 013393.python.hook-ffpyplayer.line9.comment
# 013394.python.hook-ffpyplayer.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013395.python.hook-ffpyplayer.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import eval_statement, collect_submodules

hiddenimports = collect_submodules("ffpyplayer")
binaries = []
# 013396.python.hook-ffpyplayer.line17.comment ffpyplayer has an internal variable tells us where the libraries it was using
for bin in eval_statement("import ffpyplayer; print(ffpyplayer.dep_bins)"):
    binaries += [(bin, '.')]
