# 018309.python.hook-uvicorn.line1.comment ------------------------------------------------------------------
# 018310.python.hook-uvicorn.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 018311.python.hook-uvicorn.line3.comment
# 018312.python.hook-uvicorn.line4.comment This file is distributed under the terms of the GNU General Public
# 018313.python.hook-uvicorn.line5.comment License (version 2.0 or later).
# 018314.python.hook-uvicorn.line6.comment
# 018315.python.hook-uvicorn.line7.comment The full license is available in LICENSE, distributed with
# 018316.python.hook-uvicorn.line8.comment this software.
# 018317.python.hook-uvicorn.line9.comment
# 018318.python.hook-uvicorn.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018319.python.hook-uvicorn.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('uvicorn')
