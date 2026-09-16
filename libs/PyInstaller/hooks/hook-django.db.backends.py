# 005425.python.hook-django.db.backends.line1.comment -----------------------------------------------------------------------------
# 005426.python.hook-django.db.backends.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005427.python.hook-django.db.backends.line3.comment
# 005428.python.hook-django.db.backends.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005429.python.hook-django.db.backends.line5.comment or later) with exception for distributing the bootloader.
# 005430.python.hook-django.db.backends.line6.comment
# 005431.python.hook-django.db.backends.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005432.python.hook-django.db.backends.line8.comment
# 005433.python.hook-django.db.backends.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005434.python.hook-django.db.backends.line10.comment -----------------------------------------------------------------------------

import glob
import os

from PyInstaller.utils.hooks import get_module_file_attribute

# 005435.python.hook-django.db.backends.line17.comment Compiler (see class BaseDatabaseOperations)
hiddenimports = ['django.db.models.sql.compiler']

# 005436.python.hook-django.db.backends.line20.comment Include all available Django backends.
modpath = os.path.dirname(get_module_file_attribute('django.db.backends'))
for fn in glob.glob(os.path.join(modpath, '*')):
    if os.path.isdir(fn):
        fn = os.path.basename(fn)
        hiddenimports.append('django.db.backends.' + fn + '.base')
