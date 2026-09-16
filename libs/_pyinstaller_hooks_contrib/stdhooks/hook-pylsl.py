# 015945.python.hook-pylsl.line1.comment ------------------------------------------------------------------
# 015946.python.hook-pylsl.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015947.python.hook-pylsl.line3.comment
# 015948.python.hook-pylsl.line4.comment This file is distributed under the terms of the GNU General Public
# 015949.python.hook-pylsl.line5.comment License (version 2.0 or later).
# 015950.python.hook-pylsl.line6.comment
# 015951.python.hook-pylsl.line7.comment The full license is available in LICENSE, distributed with
# 015952.python.hook-pylsl.line8.comment this software.
# 015953.python.hook-pylsl.line9.comment
# 015954.python.hook-pylsl.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015955.python.hook-pylsl.line11.comment ------------------------------------------------------------------

import os
from PyInstaller.utils.hooks import logger, isolated


def find_library():
    # 015956.python.hook-pylsl.line18.comment Try importing pylsl - this will fail if the shared library is unavailable.
    try:
        import pylsl  # noqa: F401
    except Exception:
        return None

    # 015958.python.hook-pylsl.line24.comment Return the path to shared library that is used by pylsl.
    try:
        from pylsl.lib import lib as cdll  # pylsl >= 0.17.0
    except ImportError:
        from pylsl.pylsl import lib as cdll  # older versions

    return cdll._name


# 015961.python.hook-pylsl.line33.comment whenever a hook needs to load a 3rd party library, it needs to be done in an isolated subprocess
libfile = isolated.call(find_library)

if libfile:
    # 015962.python.hook-pylsl.line37.comment add the liblsl library to the binaries
    # 015963.python.hook-pylsl.line38.comment it gets packaged in pylsl/lib, which is where pylsl will look first
    binaries = [(libfile, os.path.join('pylsl', 'lib'))]
else:
    logger.warning("liblsl shared library not found - pylsl will likely fail to work!")
    binaries = []
