# 013574.python.hook-gitlab.line1.comment ------------------------------------------------------------------
# 013575.python.hook-gitlab.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 013576.python.hook-gitlab.line3.comment
# 013577.python.hook-gitlab.line4.comment This file is distributed under the terms of the GNU General Public
# 013578.python.hook-gitlab.line5.comment License (version 2.0 or later).
# 013579.python.hook-gitlab.line6.comment
# 013580.python.hook-gitlab.line7.comment The full license is available in LICENSE, distributed with
# 013581.python.hook-gitlab.line8.comment this software.
# 013582.python.hook-gitlab.line9.comment
# 013583.python.hook-gitlab.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013584.python.hook-gitlab.line11.comment ------------------------------------------------------------------
# 013585.python.hook-gitlab.line12.comment
# 013586.python.hook-gitlab.line13.comment python-gitlab is a Python package providing access to the GitLab server API.
# 013587.python.hook-gitlab.line14.comment It supports the v4 API of GitLab, and provides a CLI tool (gitlab).
# 013588.python.hook-gitlab.line15.comment
# 013589.python.hook-gitlab.line16.comment https://python-gitlab.readthedocs.io
# 013590.python.hook-gitlab.line17.comment
# 013591.python.hook-gitlab.line18.comment Tested with gitlab 3.2.0

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('gitlab')
