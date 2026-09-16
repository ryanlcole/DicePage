# 017371.python.hook-tables.line1.comment ------------------------------------------------------------------
# 017372.python.hook-tables.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017373.python.hook-tables.line3.comment
# 017374.python.hook-tables.line4.comment This file is distributed under the terms of the GNU General Public
# 017375.python.hook-tables.line5.comment License (version 2.0 or later).
# 017376.python.hook-tables.line6.comment
# 017377.python.hook-tables.line7.comment The full license is available in LICENSE, distributed with
# 017378.python.hook-tables.line8.comment this software.
# 017379.python.hook-tables.line9.comment
# 017380.python.hook-tables.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017381.python.hook-tables.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import collect_dynamic_libs, is_module_satisfies

# 017382.python.hook-tables.line16.comment PyTables is a package for managing hierarchical datasets
hiddenimports = ["tables._comp_lzo", "tables._comp_bzip2"]

# 017383.python.hook-tables.line19.comment Collect the bundled copy of blosc2 shared library.
binaries = collect_dynamic_libs('tables')
datas = []

# 017384.python.hook-tables.line23.comment tables 3.7.0 started using `delvewheel` for its Windows PyPI wheels. While contemporary PyInstaller versions
# 017385.python.hook-tables.line24.comment automatically pick up DLLs from external `pyproj.libs` directory, this does not work on Anaconda python 3.8 and 3.9
# 017386.python.hook-tables.line25.comment due to defunct `os.add_dll_directory`, which forces `delvewheel` to use the old load-order file approach. So we need
# 017387.python.hook-tables.line26.comment to explicitly ensure that load-order file as well as DLLs are collected.
if is_win and is_module_satisfies("tables >= 3.7.0"):
    if is_module_satisfies("PyInstaller >= 5.6"):
        from PyInstaller.utils.hooks import collect_delvewheel_libs_directory
        datas, binaries = collect_delvewheel_libs_directory("tables", datas=datas, binaries=binaries)
