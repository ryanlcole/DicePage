# 012148.python.hook-avro.line1.comment ------------------------------------------------------------------
# 012149.python.hook-avro.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012150.python.hook-avro.line3.comment
# 012151.python.hook-avro.line4.comment This file is distributed under the terms of the GNU General Public
# 012152.python.hook-avro.line5.comment License (version 2.0 or later).
# 012153.python.hook-avro.line6.comment
# 012154.python.hook-avro.line7.comment The full license is available in LICENSE, distributed with
# 012155.python.hook-avro.line8.comment this software.
# 012156.python.hook-avro.line9.comment
# 012157.python.hook-avro.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012158.python.hook-avro.line11.comment ------------------------------------------------------------------
"""
Avro is a serialization and RPC framework.
"""

import os
from PyInstaller.utils.hooks import get_module_file_attribute

res_loc = os.path.dirname(get_module_file_attribute("avro"))
# 012159.python.hook-avro.line20.comment see https://github.com/apache/avro/blob/master/lang/py3/setup.py
datas = [
    # 012160.python.hook-avro.line22.comment Include the version.txt file, used to set __version__
    (os.path.join(res_loc, "VERSION.txt"), "avro"),
    # 012161.python.hook-avro.line24.comment The handshake schema is needed for IPC communication
    (os.path.join(res_loc, "HandshakeRequest.avsc"), "avro"),
    (os.path.join(res_loc, "HandshakeResponse.avsc"), "avro"),
]
