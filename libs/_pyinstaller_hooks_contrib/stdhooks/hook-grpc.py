# 013807.python.hook-grpc.line1.comment ------------------------------------------------------------------
# 013808.python.hook-grpc.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 013809.python.hook-grpc.line3.comment
# 013810.python.hook-grpc.line4.comment This file is distributed under the terms of the GNU General Public
# 013811.python.hook-grpc.line5.comment License (version 2.0 or later).
# 013812.python.hook-grpc.line6.comment
# 013813.python.hook-grpc.line7.comment The full license is available in LICENSE, distributed with
# 013814.python.hook-grpc.line8.comment this software.
# 013815.python.hook-grpc.line9.comment
# 013816.python.hook-grpc.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013817.python.hook-grpc.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('grpc')
