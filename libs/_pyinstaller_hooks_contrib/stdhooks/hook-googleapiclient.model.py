# 013730.python.hook-googleapiclient.model.line1.comment ------------------------------------------------------------------
# 013731.python.hook-googleapiclient.model.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 013732.python.hook-googleapiclient.model.line3.comment
# 013733.python.hook-googleapiclient.model.line4.comment This file is distributed under the terms of the GNU General Public
# 013734.python.hook-googleapiclient.model.line5.comment License (version 2.0 or later).
# 013735.python.hook-googleapiclient.model.line6.comment
# 013736.python.hook-googleapiclient.model.line7.comment The full license is available in LICENSE, distributed with
# 013737.python.hook-googleapiclient.model.line8.comment this software.
# 013738.python.hook-googleapiclient.model.line9.comment
# 013739.python.hook-googleapiclient.model.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013740.python.hook-googleapiclient.model.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.hooks import collect_data_files

# 013741.python.hook-googleapiclient.model.line16.comment googleapiclient.model queries the library version via
# 013742.python.hook-googleapiclient.model.line17.comment pkg_resources.get_distribution("google-api-python-client").version,
# 013743.python.hook-googleapiclient.model.line18.comment so we need to collect that package's metadata
datas = copy_metadata('google_api_python_client')
datas += collect_data_files('googleapiclient.discovery_cache', excludes=['*.txt', '**/__pycache__'])
