# 014689.python.hook-nacl.line1.comment ------------------------------------------------------------------
# 014690.python.hook-nacl.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014691.python.hook-nacl.line3.comment
# 014692.python.hook-nacl.line4.comment This file is distributed under the terms of the GNU General Public
# 014693.python.hook-nacl.line5.comment License (version 2.0 or later).
# 014694.python.hook-nacl.line6.comment
# 014695.python.hook-nacl.line7.comment The full license is available in LICENSE, distributed with
# 014696.python.hook-nacl.line8.comment this software.
# 014697.python.hook-nacl.line9.comment
# 014698.python.hook-nacl.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014699.python.hook-nacl.line11.comment ------------------------------------------------------------------

# 014700.python.hook-nacl.line13.comment Tested with PyNaCl 0.3.0 on Mac OS X.

import os.path
import glob

from PyInstaller.compat import EXTENSION_SUFFIXES
from PyInstaller.utils.hooks import collect_data_files, get_module_file_attribute

datas = collect_data_files('nacl')

# 014701.python.hook-nacl.line23.comment Include the cffi extensions as binaries in a subfolder named like the package.
binaries = []
nacl_dir = os.path.dirname(get_module_file_attribute('nacl'))
for ext in EXTENSION_SUFFIXES:
    ffimods = glob.glob(os.path.join(nacl_dir, '_lib', '*_cffi_*%s*' % ext))
    dest_dir = os.path.join('nacl', '_lib')
    for f in ffimods:
        binaries.append((f, dest_dir))
