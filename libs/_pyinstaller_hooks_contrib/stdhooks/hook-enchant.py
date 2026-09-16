# 013108.python.hook-enchant.line1.comment ------------------------------------------------------------------
# 013109.python.hook-enchant.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013110.python.hook-enchant.line3.comment
# 013111.python.hook-enchant.line4.comment This file is distributed under the terms of the GNU General Public
# 013112.python.hook-enchant.line5.comment License (version 2.0 or later).
# 013113.python.hook-enchant.line6.comment
# 013114.python.hook-enchant.line7.comment The full license is available in LICENSE, distributed with
# 013115.python.hook-enchant.line8.comment this software.
# 013116.python.hook-enchant.line9.comment
# 013117.python.hook-enchant.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013118.python.hook-enchant.line11.comment ------------------------------------------------------------------
"""
Import hook for PyEnchant.

Tested with PyEnchant 1.6.6.
"""

import os

from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks import exec_statement, collect_data_files, \
    collect_dynamic_libs, get_installer

# 013119.python.hook-enchant.line24.comment TODO Add Linux support
# 013120.python.hook-enchant.line25.comment Collect first all files that were installed directly into pyenchant
# 013121.python.hook-enchant.line26.comment package directory and this includes:
# 013122.python.hook-enchant.line27.comment - Windows: libenchat-1.dll, libenchat_ispell.dll, libenchant_myspell.dll, other
# 013123.python.hook-enchant.line28.comment dependent dlls and dictionaries for several languages (de, en, fr)
# 013124.python.hook-enchant.line29.comment - Mac OS X: usually libenchant.dylib and several dictionaries when installed via pip.
binaries = collect_dynamic_libs('enchant')
datas = collect_data_files('enchant')
excludedimports = ['enchant.tests']

# 013125.python.hook-enchant.line34.comment On OS X try to find files from Homebrew or Macports environments.
if is_darwin:
    # 013126.python.hook-enchant.line36.comment Note: env. var. ENCHANT_PREFIX_DIR is implemented only in the development version:
    # 013127.python.hook-enchant.line37.comment https://github.com/AbiWord/enchant
    # 013128.python.hook-enchant.line38.comment https://github.com/AbiWord/enchant/pull/2
    # 013129.python.hook-enchant.line39.comment TODO Test this hook with development version of enchant.
    libenchant = exec_statement("""
        from enchant._enchant import e
        print(e._name)
    """).strip()

    installer = get_installer('enchant')
    if installer != 'pip':
        # 013130.python.hook-enchant.line47.comment Note: Name of detected enchant library is 'libenchant.dylib'. However, it
        # 013131.python.hook-enchant.line48.comment is just symlink to 'libenchant.1.dylib'.
        binaries.append((libenchant, '.'))

        # 013132.python.hook-enchant.line51.comment Collect enchant backends from Macports. Using same file structure as on Windows.
        backends = exec_statement("""
            from enchant import Broker
            for provider in Broker().describe():
                print(provider.file)""").strip().split()
        binaries.extend([(b, 'enchant/lib/enchant') for b in backends])

        # 013133.python.hook-enchant.line58.comment Collect all available dictionaries from Macports. Using same file structure as on Windows.
        # 013134.python.hook-enchant.line59.comment In Macports are available mostly hunspell (myspell) and aspell dictionaries.
        libdir = os.path.dirname(libenchant)  # e.g. /opt/local/lib
        sharedir = os.path.join(os.path.dirname(libdir), 'share')  # e.g. /opt/local/share
        if os.path.exists(os.path.join(sharedir, 'enchant')):
            datas.append((os.path.join(sharedir, 'enchant'), 'enchant/share/enchant'))
        if os.path.exists(os.path.join(sharedir, 'enchant-2')):
            datas.append((os.path.join(sharedir, 'enchant-2'), 'enchant/share/enchant-2'))
