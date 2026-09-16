# 011768.python.hook-Cryptodome.line1.comment ------------------------------------------------------------------
# 011769.python.hook-Cryptodome.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011770.python.hook-Cryptodome.line3.comment
# 011771.python.hook-Cryptodome.line4.comment This file is distributed under the terms of the GNU General Public
# 011772.python.hook-Cryptodome.line5.comment License (version 2.0 or later).
# 011773.python.hook-Cryptodome.line6.comment
# 011774.python.hook-Cryptodome.line7.comment The full license is available in LICENSE, distributed with
# 011775.python.hook-Cryptodome.line8.comment this software.
# 011776.python.hook-Cryptodome.line9.comment
# 011777.python.hook-Cryptodome.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011778.python.hook-Cryptodome.line11.comment ------------------------------------------------------------------
"""
Hook for Cryptodome module: https://pypi.python.org/pypi/pycryptodomex

Tested with Cryptodomex 3.4.2, Python 2.7 & 3.5, Windows
"""

import os
import glob

from PyInstaller.compat import EXTENSION_SUFFIXES
from PyInstaller.utils.hooks import get_module_file_attribute

# 011779.python.hook-Cryptodome.line24.comment Include the modules as binaries in a subfolder named like the package.
# 011780.python.hook-Cryptodome.line25.comment Cryptodome's loader expects to find them inside the package directory for
# 011781.python.hook-Cryptodome.line26.comment the main module. We cannot use hiddenimports because that would add the
# 011782.python.hook-Cryptodome.line27.comment modules outside the package.

binaries = []
binary_module_names = [
    'Cryptodome.Cipher',
    'Cryptodome.Util',
    'Cryptodome.Hash',
    'Cryptodome.Protocol',
    'Cryptodome.Math',
    'Cryptodome.PublicKey',
]

for module_name in binary_module_names:
    m_dir = os.path.dirname(get_module_file_attribute(module_name))
    for ext in EXTENSION_SUFFIXES:
        module_bin = glob.glob(os.path.join(m_dir, '_*%s' % ext))
        for f in module_bin:
            binaries.append((f, module_name.replace('.', '/')))
