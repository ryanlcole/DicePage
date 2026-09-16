# 016489.python.hook-rlp.line1.comment ------------------------------------------------------------------
# 016490.python.hook-rlp.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016491.python.hook-rlp.line3.comment
# 016492.python.hook-rlp.line4.comment This file is distributed under the terms of the GNU General Public
# 016493.python.hook-rlp.line5.comment License (version 2.0 or later).
# 016494.python.hook-rlp.line6.comment
# 016495.python.hook-rlp.line7.comment The full license is available in LICENSE, distributed with
# 016496.python.hook-rlp.line8.comment this software.
# 016497.python.hook-rlp.line9.comment
# 016498.python.hook-rlp.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016499.python.hook-rlp.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, copy_metadata

# 016500.python.hook-rlp.line15.comment Starting with v4.0.0, `rlp` queries its version from metadata.
if is_module_satisfies("rlp >= 4.0.0"):
    datas = copy_metadata('rlp')
