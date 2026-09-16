# 012955.python.hook-discid.line1.comment ------------------------------------------------------------------
# 012956.python.hook-discid.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 012957.python.hook-discid.line3.comment
# 012958.python.hook-discid.line4.comment This file is distributed under the terms of the GNU General Public
# 012959.python.hook-discid.line5.comment License (version 2.0 or later).
# 012960.python.hook-discid.line6.comment
# 012961.python.hook-discid.line7.comment The full license is available in LICENSE, distributed with
# 012962.python.hook-discid.line8.comment this software.
# 012963.python.hook-discid.line9.comment
# 012964.python.hook-discid.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012965.python.hook-discid.line11.comment ------------------------------------------------------------------

import os

from PyInstaller.utils.hooks import get_module_attribute, logger
from PyInstaller.depend.utils import _resolveCtypesImports

binaries = []

# 012966.python.hook-discid.line20.comment Use the _LIB_NAME attribute of discid.libdiscid to resolve the shared library name. This saves us from having to
# 012967.python.hook-discid.line21.comment duplicate the name guessing logic from discid.libdiscid.
# 012968.python.hook-discid.line22.comment On error, PyInstaller >= 5.0 raises exception, earlier versions return an empty string.
try:
    lib_name = get_module_attribute("discid.libdiscid", "_LIB_NAME")
except Exception:
    lib_name = None

if lib_name:
    lib_name = os.path.basename(lib_name)
    try:
        resolved_binary = _resolveCtypesImports([lib_name])
        lib_file = resolved_binary[0][1]
    except Exception as e:
        lib_file = None
        logger.warning("Error while trying to resolve %s: %s", lib_name, e)

    if lib_file:
        binaries += [(lib_file, '.')]
else:
    logger.warning("Failed to determine name of libdiscid shared library from _LIB_NAME attribute of discid.libdiscid!")
