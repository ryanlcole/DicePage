# 014086.python.hook-jira.line1.comment ------------------------------------------------------------------
# 014087.python.hook-jira.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014088.python.hook-jira.line3.comment
# 014089.python.hook-jira.line4.comment This file is distributed under the terms of the GNU General Public
# 014090.python.hook-jira.line5.comment License (version 2.0 or later).
# 014091.python.hook-jira.line6.comment
# 014092.python.hook-jira.line7.comment The full license is available in LICENSE, distributed with
# 014093.python.hook-jira.line8.comment this software.
# 014094.python.hook-jira.line9.comment
# 014095.python.hook-jira.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014096.python.hook-jira.line11.comment ------------------------------------------------------------------
"""
Hook for https://pypi.python.org/pypi/jira/
"""

from PyInstaller.utils.hooks import copy_metadata, collect_submodules

datas = copy_metadata('jira')
hiddenimports = collect_submodules('jira')
