# 012091.python.hook-astropy.line1.comment ------------------------------------------------------------------
# 012092.python.hook-astropy.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012093.python.hook-astropy.line3.comment
# 012094.python.hook-astropy.line4.comment This file is distributed under the terms of the GNU General Public
# 012095.python.hook-astropy.line5.comment License (version 2.0 or later).
# 012096.python.hook-astropy.line6.comment
# 012097.python.hook-astropy.line7.comment The full license is available in LICENSE, distributed with
# 012098.python.hook-astropy.line8.comment this software.
# 012099.python.hook-astropy.line9.comment
# 012100.python.hook-astropy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012101.python.hook-astropy.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, \
    copy_metadata, is_module_satisfies

# 012102.python.hook-astropy.line16.comment Astropy includes a number of non-Python files that need to be present
# 012103.python.hook-astropy.line17.comment at runtime, so we include these explicitly here.
datas = collect_data_files('astropy')

# 012104.python.hook-astropy.line20.comment In a number of places, astropy imports other sub-modules in a way that is not
# 012105.python.hook-astropy.line21.comment always auto-discovered by pyinstaller, so we always include all submodules.
hiddenimports = collect_submodules('astropy')

# 012106.python.hook-astropy.line24.comment We now need to include the *_parsetab.py and *_lextab.py files for unit and
# 012107.python.hook-astropy.line25.comment coordinate parsing, since these are loaded as files rather than imported as
# 012108.python.hook-astropy.line26.comment sub-modules. We leverage collect_data_files to get all files in astropy then
# 012109.python.hook-astropy.line27.comment filter these.
ply_files = []
for path, target in collect_data_files('astropy', include_py_files=True):
    if path.endswith(('_parsetab.py', '_lextab.py')):
        ply_files.append((path, target))

datas += ply_files

# 012110.python.hook-astropy.line35.comment Astropy version >= 5.0 queries metadata to get version information.
if is_module_satisfies('astropy >= 5.0'):
    datas += copy_metadata('astropy')
    datas += copy_metadata('numpy')

# 012111.python.hook-astropy.line40.comment In the Cython code, Astropy imports numpy.lib.recfunctions which isn't
# 012112.python.hook-astropy.line41.comment automatically discovered by pyinstaller, so we add this as a hidden import.
hiddenimports += ['numpy.lib.recfunctions']
