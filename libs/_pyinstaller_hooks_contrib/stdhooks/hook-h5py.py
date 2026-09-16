# 013858.python.hook-h5py.line1.comment ------------------------------------------------------------------
# 013859.python.hook-h5py.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013860.python.hook-h5py.line3.comment
# 013861.python.hook-h5py.line4.comment This file is distributed under the terms of the GNU General Public
# 013862.python.hook-h5py.line5.comment License (version 2.0 or later).
# 013863.python.hook-h5py.line6.comment
# 013864.python.hook-h5py.line7.comment The full license is available in LICENSE, distributed with
# 013865.python.hook-h5py.line8.comment this software.
# 013866.python.hook-h5py.line9.comment
# 013867.python.hook-h5py.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013868.python.hook-h5py.line11.comment ------------------------------------------------------------------
"""
Hook for http://pypi.python.org/pypi/h5py/
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("h5py", lambda x: "tests" not in x)
