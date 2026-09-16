# 007077.python.hook-pyi_splash.line1.comment -----------------------------------------------------------------------------
# 007078.python.hook-pyi_splash.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007079.python.hook-pyi_splash.line3.comment
# 007080.python.hook-pyi_splash.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007081.python.hook-pyi_splash.line5.comment or later) with exception for distributing the bootloader.
# 007082.python.hook-pyi_splash.line6.comment
# 007083.python.hook-pyi_splash.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007084.python.hook-pyi_splash.line8.comment
# 007085.python.hook-pyi_splash.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007086.python.hook-pyi_splash.line10.comment -----------------------------------------------------------------------------
"""
This hook does not move a module that can be installed by a package manager, but points to a PyInstaller internal
module that can be imported into the users python instance.

The module is implemented in 'PyInstaller/fake-modules/pyi_splash.py'.
"""

import os

from PyInstaller import PACKAGEPATH
from PyInstaller.utils.hooks import logger


def pre_find_module_path(api):
    try:
        # 007087.python.hook-pyi_splash.line26.comment Test if a module named 'pyi_splash' is locally installed. This prevents that a potentially required dependency
        # 007088.python.hook-pyi_splash.line27.comment is not packed
        import pyi_splash  # noqa: F401
    except ImportError:
        module_dir = os.path.join(PACKAGEPATH, 'fake-modules')

        api.search_dirs = [module_dir]
        logger.info('Adding pyi_splash module to application dependencies.')
    else:
        logger.info('A local module named "pyi_splash" is installed. Use the installed one instead.')
        return
