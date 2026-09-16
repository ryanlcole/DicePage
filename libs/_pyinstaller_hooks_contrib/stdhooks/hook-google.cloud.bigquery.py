# 013649.python.hook-google.cloud.bigquery.line1.comment ------------------------------------------------------------------
# 013650.python.hook-google.cloud.bigquery.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013651.python.hook-google.cloud.bigquery.line3.comment
# 013652.python.hook-google.cloud.bigquery.line4.comment This file is distributed under the terms of the GNU General Public
# 013653.python.hook-google.cloud.bigquery.line5.comment License (version 2.0 or later).
# 013654.python.hook-google.cloud.bigquery.line6.comment
# 013655.python.hook-google.cloud.bigquery.line7.comment The full license is available in LICENSE, distributed with
# 013656.python.hook-google.cloud.bigquery.line8.comment this software.
# 013657.python.hook-google.cloud.bigquery.line9.comment
# 013658.python.hook-google.cloud.bigquery.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013659.python.hook-google.cloud.bigquery.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata
datas = (copy_metadata('google-cloud-bigquery') +
         # 013660.python.hook-google.cloud.bigquery.line15.comment the pakcage queries meta-data about ``request``
         copy_metadata('requests'))
