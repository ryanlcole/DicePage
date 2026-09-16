# 013242.python.hook-eth_typing.line1.comment ------------------------------------------------------------------
# 013243.python.hook-eth_typing.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 013244.python.hook-eth_typing.line3.comment
# 013245.python.hook-eth_typing.line4.comment This file is distributed under the terms of the GNU General Public
# 013246.python.hook-eth_typing.line5.comment License (version 2.0 or later).
# 013247.python.hook-eth_typing.line6.comment
# 013248.python.hook-eth_typing.line7.comment The full license is available in LICENSE, distributed with
# 013249.python.hook-eth_typing.line8.comment this software.
# 013250.python.hook-eth_typing.line9.comment
# 013251.python.hook-eth_typing.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013252.python.hook-eth_typing.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata

# 013253.python.hook-eth_typing.line15.comment eth-typing queries it's own version using importlib.metadata/pkg_resources.
datas = copy_metadata("eth-typing")
