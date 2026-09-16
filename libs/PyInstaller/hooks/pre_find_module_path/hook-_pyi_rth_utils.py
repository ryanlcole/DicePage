# 007050.python.hook-_pyi_rth_utils.line1.comment -----------------------------------------------------------------------------
# 007051.python.hook-_pyi_rth_utils.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 007052.python.hook-_pyi_rth_utils.line3.comment
# 007053.python.hook-_pyi_rth_utils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007054.python.hook-_pyi_rth_utils.line5.comment or later) with exception for distributing the bootloader.
# 007055.python.hook-_pyi_rth_utils.line6.comment
# 007056.python.hook-_pyi_rth_utils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007057.python.hook-_pyi_rth_utils.line8.comment
# 007058.python.hook-_pyi_rth_utils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007059.python.hook-_pyi_rth_utils.line10.comment -----------------------------------------------------------------------------
"""
This hook allows discovery and collection of PyInstaller's internal _pyi_rth_utils module that provides utility
functions for run-time hooks.

The module is implemented in 'PyInstaller/fake-modules/_pyi_rth_utils.py'.
"""

import os

from PyInstaller import PACKAGEPATH


def pre_find_module_path(api):
    module_dir = os.path.join(PACKAGEPATH, 'fake-modules')
    api.search_dirs = [module_dir]
