# 015394.python.hook-pptx.line1.comment ------------------------------------------------------------------
# 015395.python.hook-pptx.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 015396.python.hook-pptx.line3.comment
# 015397.python.hook-pptx.line4.comment This file is distributed under the terms of the GNU General Public
# 015398.python.hook-pptx.line5.comment License (version 2.0 or later).
# 015399.python.hook-pptx.line6.comment
# 015400.python.hook-pptx.line7.comment The full license is available in LICENSE, distributed with
# 015401.python.hook-pptx.line8.comment this software.
# 015402.python.hook-pptx.line9.comment
# 015403.python.hook-pptx.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015404.python.hook-pptx.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pptx.templates')
