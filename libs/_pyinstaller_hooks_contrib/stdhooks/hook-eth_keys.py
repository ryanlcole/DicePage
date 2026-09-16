# 013218.python.hook-eth_keys.line1.comment ------------------------------------------------------------------
# 013219.python.hook-eth_keys.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 013220.python.hook-eth_keys.line3.comment
# 013221.python.hook-eth_keys.line4.comment This file is distributed under the terms of the GNU General Public
# 013222.python.hook-eth_keys.line5.comment License (version 2.0 or later).
# 013223.python.hook-eth_keys.line6.comment
# 013224.python.hook-eth_keys.line7.comment The full license is available in LICENSE, distributed with
# 013225.python.hook-eth_keys.line8.comment this software.
# 013226.python.hook-eth_keys.line9.comment
# 013227.python.hook-eth_keys.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013228.python.hook-eth_keys.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, is_module_satisfies

# 013229.python.hook-eth_keys.line15.comment As of eth-keys 0.5.0, it uses importlib.metadata.version() set its __version__ attribute
if is_module_satisfies("eth-keys >= 0.5.0"):
    datas = copy_metadata("eth-keys")
