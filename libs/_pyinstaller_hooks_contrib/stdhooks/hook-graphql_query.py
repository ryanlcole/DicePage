# 013755.python.hook-graphql_query.line1.comment -----------------------------------------------------------------------------
# 013756.python.hook-graphql_query.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 013757.python.hook-graphql_query.line3.comment
# 013758.python.hook-graphql_query.line4.comment This file is distributed under the terms of the GNU General Public
# 013759.python.hook-graphql_query.line5.comment License (version 2.0 or later).
# 013760.python.hook-graphql_query.line6.comment
# 013761.python.hook-graphql_query.line7.comment The full license is available in LICENSE, distributed with
# 013762.python.hook-graphql_query.line8.comment this software.
# 013763.python.hook-graphql_query.line9.comment
# 013764.python.hook-graphql_query.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013765.python.hook-graphql_query.line11.comment -----------------------------------------------------------------------------
"""
PyInstaller hook file for graphql_query. Tested with version 1.0.3.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('graphql_query')
