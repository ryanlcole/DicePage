# 001875.python.config.line1.comment -----------------------------------------------------------------------------
# 001876.python.config.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 001877.python.config.line3.comment
# 001878.python.config.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 001879.python.config.line5.comment or later) with exception for distributing the bootloader.
# 001880.python.config.line6.comment
# 001881.python.config.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 001882.python.config.line8.comment
# 001883.python.config.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 001884.python.config.line10.comment -----------------------------------------------------------------------------
"""
This module holds run-time PyInstaller configuration.

Variable CONF is a dict() with all configuration options that are necessary for the build phase. Build phase is done by
passing .spec file to exec() function. CONF variable is the only way how to pass arguments to exec() and how to avoid
using 'global' variables.

NOTE: Having 'global' variables does not play well with the test suite because it does not provide isolated environments
for tests. Some tests might fail in this case.

NOTE: The 'CONF' dict() is cleaned after building phase to not interfere with any other possible test.

To pass any arguments to build phase, just do:

    from PyInstaller.config import CONF
    CONF['my_var_name'] = my_value

And to use this variable in the build phase:

    from PyInstaller.config import CONF
    foo = CONF['my_var_name']


This is the list of known variables. (Please update it if necessary.)

cachedir
hiddenimports
noconfirm
pathex
ui_admin
ui_access
upx_available
upx_dir
workpath

tests_modgraph  - cached PyiModuleGraph object to speed up tests

code_cache - dictionary associating `Analysis.pure` list instances with code cache dictionaries. Used by PYZ writer.
"""

# 001885.python.config.line51.comment NOTE: Do not import other PyInstaller modules here. Just define constants here.

CONF = {
    # 001886.python.config.line54.comment Unit tests require this key to exist.
    'pathex': [],
}
