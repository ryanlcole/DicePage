# 020151.python.hook-wx.lib.pubsub.line1.comment ------------------------------------------------------------------
# 020152.python.hook-wx.lib.pubsub.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020153.python.hook-wx.lib.pubsub.line3.comment
# 020154.python.hook-wx.lib.pubsub.line4.comment This file is distributed under the terms of the GNU General Public
# 020155.python.hook-wx.lib.pubsub.line5.comment License (version 2.0 or later).
# 020156.python.hook-wx.lib.pubsub.line6.comment
# 020157.python.hook-wx.lib.pubsub.line7.comment The full license is available in LICENSE, distributed with
# 020158.python.hook-wx.lib.pubsub.line8.comment this software.
# 020159.python.hook-wx.lib.pubsub.line9.comment
# 020160.python.hook-wx.lib.pubsub.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020161.python.hook-wx.lib.pubsub.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('wx.lib.pubsub', include_py_files=True, excludes=['*.txt', '**/__pycache__'])
