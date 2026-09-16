# 011751.python.hook-Crypto.line1.comment ------------------------------------------------------------------
# 011752.python.hook-Crypto.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011753.python.hook-Crypto.line3.comment
# 011754.python.hook-Crypto.line4.comment This file is distributed under the terms of the GNU General Public
# 011755.python.hook-Crypto.line5.comment License (version 2.0 or later).
# 011756.python.hook-Crypto.line6.comment
# 011757.python.hook-Crypto.line7.comment The full license is available in LICENSE, distributed with
# 011758.python.hook-Crypto.line8.comment this software.
# 011759.python.hook-Crypto.line9.comment
# 011760.python.hook-Crypto.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011761.python.hook-Crypto.line11.comment ------------------------------------------------------------------
"""
Hook for PyCryptodome library: https://pypi.python.org/pypi/pycryptodome

PyCryptodome is an almost drop-in replacement for the now unmaintained
PyCrypto library. The two are mutually exclusive as they live under
the same package ("Crypto").

PyCryptodome distributes dynamic libraries and builds them as if they were
Python C extensions (even though they are not extensions - as they can't be
imported by Python). It might sound a bit weird, but this decision is rooted
in PyPy and its partial and slow support for C extensions. However, this also
invalidates several of the existing methods used by PyInstaller to decide the
right files to pull in.

Even though this hook is meant to help with PyCryptodome only, it will be
triggered also when PyCrypto is installed, so it must be tested with both.

Tested with PyCryptodome 3.5.1, PyCrypto 2.6.1, Python 2.7 & 3.6, Fedora & Windows
"""

import os
import glob

from PyInstaller.compat import EXTENSION_SUFFIXES
from PyInstaller.utils.hooks import get_module_file_attribute

# 011762.python.hook-Crypto.line38.comment Include the modules as binaries in a subfolder named like the package.
# 011763.python.hook-Crypto.line39.comment Cryptodome's loader expects to find them inside the package directory for
# 011764.python.hook-Crypto.line40.comment the main module. We cannot use hiddenimports because that would add the
# 011765.python.hook-Crypto.line41.comment modules outside the package.

binaries = []
binary_module_names = [
    'Crypto.Math',  # First in the list
    'Crypto.Cipher',
    'Crypto.Util',
    'Crypto.Hash',
    'Crypto.Protocol',
    'Crypto.PublicKey',
]

try:
    for module_name in binary_module_names:
        m_dir = os.path.dirname(get_module_file_attribute(module_name))
        for ext in EXTENSION_SUFFIXES:
            module_bin = glob.glob(os.path.join(m_dir, '_*%s' % ext))
            for f in module_bin:
                binaries.append((f, module_name.replace('.', os.sep)))
except ImportError:
    # 011767.python.hook-Crypto.line61.comment Do nothing for PyCrypto (Crypto.Math does not exist there)
    pass
