# 014678.python.hook-msoffcrypto.line1.comment ------------------------------------------------------------------
# 014679.python.hook-msoffcrypto.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 014680.python.hook-msoffcrypto.line3.comment
# 014681.python.hook-msoffcrypto.line4.comment This file is distributed under the terms of the GNU General Public
# 014682.python.hook-msoffcrypto.line5.comment License (version 2.0 or later).
# 014683.python.hook-msoffcrypto.line6.comment
# 014684.python.hook-msoffcrypto.line7.comment The full license is available in LICENSE, distributed with
# 014685.python.hook-msoffcrypto.line8.comment this software.
# 014686.python.hook-msoffcrypto.line9.comment
# 014687.python.hook-msoffcrypto.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014688.python.hook-msoffcrypto.line11.comment ------------------------------------------------------------------
"""
msoffcrypto contains hidden metadata as of v4.12.0
"""

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('msoffcrypto-tool')
