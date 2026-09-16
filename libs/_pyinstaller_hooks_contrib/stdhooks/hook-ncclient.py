# 014787.python.hook-ncclient.line1.comment ------------------------------------------------------------------
# 014788.python.hook-ncclient.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014789.python.hook-ncclient.line3.comment
# 014790.python.hook-ncclient.line4.comment This file is distributed under the terms of the GNU General Public
# 014791.python.hook-ncclient.line5.comment License (version 2.0 or later).
# 014792.python.hook-ncclient.line6.comment
# 014793.python.hook-ncclient.line7.comment The full license is available in LICENSE, distributed with
# 014794.python.hook-ncclient.line8.comment this software.
# 014795.python.hook-ncclient.line9.comment
# 014796.python.hook-ncclient.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014797.python.hook-ncclient.line11.comment ------------------------------------------------------------------
"""
Hook for ncclient. ncclient is a Python library that facilitates client-side
scripting and application development around the NETCONF protocol.
https://pypi.python.org/pypi/ncclient

This hook was tested with ncclient 0.4.3.
"""
from PyInstaller.utils.hooks import collect_submodules

# 014798.python.hook-ncclient.line21.comment Modules 'ncclient.devices.*' are dynamically loaded and PyInstaller
# 014799.python.hook-ncclient.line22.comment is not able to find them.
hiddenimports = collect_submodules('ncclient.devices')
