# 013194.python.hook-eth_hash.line1.comment ------------------------------------------------------------------
# 013195.python.hook-eth_hash.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013196.python.hook-eth_hash.line3.comment
# 013197.python.hook-eth_hash.line4.comment This file is distributed under the terms of the GNU General Public
# 013198.python.hook-eth_hash.line5.comment License (version 2.0 or later).
# 013199.python.hook-eth_hash.line6.comment
# 013200.python.hook-eth_hash.line7.comment The full license is available in LICENSE, distributed with
# 013201.python.hook-eth_hash.line8.comment this software.
# 013202.python.hook-eth_hash.line9.comment
# 013203.python.hook-eth_hash.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013204.python.hook-eth_hash.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, copy_metadata, is_module_satisfies

# 013205.python.hook-eth_hash.line15.comment The ``eth_hash.utils.load_backend`` function does a dynamic import.
hiddenimports = collect_submodules('eth_hash.backends')

# 013206.python.hook-eth_hash.line18.comment As of eth-hash 0.6.0, it uses importlib.metadata.version() set its __version__ attribute
if is_module_satisfies("eth-hash >= 0.6.0"):
    datas = copy_metadata("eth-hash")
