# 013230.python.hook-eth_rlp.line1.comment ------------------------------------------------------------------
# 013231.python.hook-eth_rlp.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 013232.python.hook-eth_rlp.line3.comment
# 013233.python.hook-eth_rlp.line4.comment This file is distributed under the terms of the GNU General Public
# 013234.python.hook-eth_rlp.line5.comment License (version 2.0 or later).
# 013235.python.hook-eth_rlp.line6.comment
# 013236.python.hook-eth_rlp.line7.comment The full license is available in LICENSE, distributed with
# 013237.python.hook-eth_rlp.line8.comment this software.
# 013238.python.hook-eth_rlp.line9.comment
# 013239.python.hook-eth_rlp.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013240.python.hook-eth_rlp.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, copy_metadata

# 013241.python.hook-eth_rlp.line15.comment Starting with v1.0.0, `eth_rlp` queries its version from metadata.
if is_module_satisfies("eth-rlp >= 1.0.0"):
    datas = copy_metadata('eth-rlp')
