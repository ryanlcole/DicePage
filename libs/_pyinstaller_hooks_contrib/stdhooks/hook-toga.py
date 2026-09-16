# 017587.python.hook-toga.line1.comment ------------------------------------------------------------------
# 017588.python.hook-toga.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017589.python.hook-toga.line3.comment
# 017590.python.hook-toga.line4.comment This file is distributed under the terms of the GNU General Public
# 017591.python.hook-toga.line5.comment License (version 2.0 or later).
# 017592.python.hook-toga.line6.comment
# 017593.python.hook-toga.line7.comment The full license is available in LICENSE, distributed with
# 017594.python.hook-toga.line8.comment this software.
# 017595.python.hook-toga.line9.comment
# 017596.python.hook-toga.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017597.python.hook-toga.line11.comment ------------------------------------------------------------------

from PyInstaller import compat
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata, is_module_satisfies

hiddenimports = []

# 017598.python.hook-toga.line18.comment Select the platform-specific backend.
if compat.is_darwin:
    backend = 'cocoa'
elif compat.is_linux:
    backend = 'gtk'
elif compat.is_win:
    backend = 'winforms'
else:
    backend = None

if backend is not None:
    hiddenimports += [f'toga_{backend}', f'toga_{backend}.factory']

# 017599.python.hook-toga.line31.comment Collect metadata for toga-core dist, which is used by toga module to determine its version.
datas = copy_metadata("toga-core")

# 017600.python.hook-toga.line34.comment Prevent `toga` from pulling `setuptools_scm` into frozen application, as it makes no sense in that context.
excludedimports = ["setuptools_scm"]

# 017601.python.hook-toga.line37.comment `toga` 0.5.0 refactored its `__init__.py` to lazy-load its core modules. Therefore, we now need to collect
# 017602.python.hook-toga.line38.comment submodules via `collect_submodules`...
if is_module_satisfies("toga >= 0.5.0"):
    hiddenimports += collect_submodules("toga")

# 017603.python.hook-toga.line42.comment Starting with `toga` 0.5.2, we need to collect .pyi files.
if is_module_satisfies("toga >= 0.5.2"):
    datas += collect_data_files("toga")
