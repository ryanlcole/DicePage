# 014108.python.hook-jsonrpcserver.line1.comment ------------------------------------------------------------------
# 014109.python.hook-jsonrpcserver.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 014110.python.hook-jsonrpcserver.line3.comment
# 014111.python.hook-jsonrpcserver.line4.comment This file is distributed under the terms of the GNU General Public
# 014112.python.hook-jsonrpcserver.line5.comment License (version 2.0 or later).
# 014113.python.hook-jsonrpcserver.line6.comment
# 014114.python.hook-jsonrpcserver.line7.comment The full license is available in LICENSE, distributed with
# 014115.python.hook-jsonrpcserver.line8.comment this software.
# 014116.python.hook-jsonrpcserver.line9.comment
# 014117.python.hook-jsonrpcserver.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014118.python.hook-jsonrpcserver.line11.comment ------------------------------------------------------------------

# 014119.python.hook-jsonrpcserver.line13.comment This is needed to bundle request-schema.json file needed by
# 014120.python.hook-jsonrpcserver.line14.comment jsonrpcserver package

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('jsonrpcserver')
