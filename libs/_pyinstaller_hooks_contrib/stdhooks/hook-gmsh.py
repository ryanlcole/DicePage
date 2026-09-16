# 013614.python.hook-gmsh.line1.comment ------------------------------------------------------------------
# 013615.python.hook-gmsh.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 013616.python.hook-gmsh.line3.comment
# 013617.python.hook-gmsh.line4.comment This file is distributed under the terms of the GNU General Public
# 013618.python.hook-gmsh.line5.comment License (version 2.0 or later).
# 013619.python.hook-gmsh.line6.comment
# 013620.python.hook-gmsh.line7.comment The full license is available in LICENSE, distributed with
# 013621.python.hook-gmsh.line8.comment this software.
# 013622.python.hook-gmsh.line9.comment
# 013623.python.hook-gmsh.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013624.python.hook-gmsh.line11.comment ------------------------------------------------------------------

import os

from PyInstaller.utils.hooks import logger, get_module_attribute

# 013625.python.hook-gmsh.line17.comment Query the `libpath` attribute of the `gmsh` module to obtain the path to shared library. This way, we do not need to
# 013626.python.hook-gmsh.line18.comment duplicate the discovery logic.
try:
    lib_file = get_module_attribute('gmsh', 'libpath')
except Exception:
    logger.warning("Failed to query gmsh.libpath!", exc_info=True)
    lib_file = None

if lib_file and os.path.isfile(lib_file):
    binaries = [(lib_file, '.')]
else:
    logger.warning("Could not find gmsh shared library - gmsh will likely fail to load at run-time!")
