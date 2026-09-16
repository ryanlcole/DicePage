# 011725.python.hook-BTrees.line1.comment ------------------------------------------------------------------
# 011726.python.hook-BTrees.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011727.python.hook-BTrees.line3.comment
# 011728.python.hook-BTrees.line4.comment This file is distributed under the terms of the GNU General Public
# 011729.python.hook-BTrees.line5.comment License (version 2.0 or later).
# 011730.python.hook-BTrees.line6.comment
# 011731.python.hook-BTrees.line7.comment The full license is available in LICENSE, distributed with
# 011732.python.hook-BTrees.line8.comment this software.
# 011733.python.hook-BTrees.line9.comment
# 011734.python.hook-BTrees.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011735.python.hook-BTrees.line11.comment ------------------------------------------------------------------

# 011736.python.hook-BTrees.line13.comment Hook for BTrees: https://pypi.org/project/BTrees/4.5.1/

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('BTrees')
