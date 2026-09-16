# 012289.python.hook-blspy.line1.comment ------------------------------------------------------------------
# 012290.python.hook-blspy.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 012291.python.hook-blspy.line3.comment
# 012292.python.hook-blspy.line4.comment This file is distributed under the terms of the GNU General Public
# 012293.python.hook-blspy.line5.comment License (version 2.0 or later).
# 012294.python.hook-blspy.line6.comment
# 012295.python.hook-blspy.line7.comment The full license is available in LICENSE, distributed with
# 012296.python.hook-blspy.line8.comment this software.
# 012297.python.hook-blspy.line9.comment
# 012298.python.hook-blspy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012299.python.hook-blspy.line11.comment ------------------------------------------------------------------

import os
import glob

from PyInstaller.utils.hooks import get_module_file_attribute
from PyInstaller.compat import is_win

# 012300.python.hook-blspy.line19.comment blspy comes as a stand-alone extension module that's placed directly
# 012301.python.hook-blspy.line20.comment in site-packages.
# 012302.python.hook-blspy.line21.comment
# 012303.python.hook-blspy.line22.comment On macOS and Linux, it is linked against the GMP library, whose shared
# 012304.python.hook-blspy.line23.comment library is stored in blspy.libs and .dylibsblspy, respectively. As this
# 012305.python.hook-blspy.line24.comment is a linked dependency, it is collected properly by PyInstaller and
# 012306.python.hook-blspy.line25.comment no further work is needed.
# 012307.python.hook-blspy.line26.comment
# 012308.python.hook-blspy.line27.comment On Windows, however, the blspy extension is linked against MPIR library,
# 012309.python.hook-blspy.line28.comment whose DLLs are placed directly into site-packages. The mpir.dll is
# 012310.python.hook-blspy.line29.comment linked dependency and is picked up automatically, but it in turn
# 012311.python.hook-blspy.line30.comment dynamically loads CPU-specific backends that are named mpir_*.dll.
# 012312.python.hook-blspy.line31.comment We need to colllect these manually.
if is_win:
    blspy_dir = os.path.dirname(get_module_file_attribute('blspy'))
    mpir_dlls = glob.glob(os.path.join(blspy_dir, 'mpir_*.dll'))
    binaries = [(mpir_dll, '.') for mpir_dll in mpir_dlls]
