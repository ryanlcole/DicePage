# 016214.python.hook-pyshark.line1.comment ------------------------------------------------------------------
# 016215.python.hook-pyshark.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016216.python.hook-pyshark.line3.comment
# 016217.python.hook-pyshark.line4.comment This file is distributed under the terms of the GNU General Public
# 016218.python.hook-pyshark.line5.comment License (version 2.0 or later).
# 016219.python.hook-pyshark.line6.comment
# 016220.python.hook-pyshark.line7.comment The full license is available in LICENSE, distributed with
# 016221.python.hook-pyshark.line8.comment this software.
# 016222.python.hook-pyshark.line9.comment
# 016223.python.hook-pyshark.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016224.python.hook-pyshark.line11.comment ------------------------------------------------------------------

# 016225.python.hook-pyshark.line13.comment Python wrapper for pyshark(https://pypi.org/project/pyshark/)
# 016226.python.hook-pyshark.line14.comment Tested with version 0.4.5

from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies

hiddenimports = ['pyshark.config']

if is_module_satisfies("pyshark < 0.6"):
    hiddenimports += ['py._path.local', 'py._vendored_packages.iniconfig']
    if is_module_satisfies("pyshark >= 0.5"):
        hiddenimports += ["py._io.terminalwriter", "py._builtin"]

datas = collect_data_files('pyshark')
