# 006370.python.hook-matplotlib.line1.comment -----------------------------------------------------------------------------
# 006371.python.hook-matplotlib.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006372.python.hook-matplotlib.line3.comment
# 006373.python.hook-matplotlib.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006374.python.hook-matplotlib.line5.comment or later) with exception for distributing the bootloader.
# 006375.python.hook-matplotlib.line6.comment
# 006376.python.hook-matplotlib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006377.python.hook-matplotlib.line8.comment
# 006378.python.hook-matplotlib.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006379.python.hook-matplotlib.line10.comment -----------------------------------------------------------------------------

from PyInstaller import isolated
from PyInstaller import compat
from PyInstaller.utils import hooks as hookutils


@isolated.decorate
def mpl_data_dir():
    import matplotlib
    return matplotlib.get_data_path()


datas = [
    (mpl_data_dir(), "matplotlib/mpl-data"),
]

binaries = []

# 006380.python.hook-matplotlib.line29.comment Windows PyPI wheels for `matplotlib` >= 3.7.0 use `delvewheel`.
# 006381.python.hook-matplotlib.line30.comment In addition to DLLs from `matplotlib.libs` directory, which should be picked up automatically by dependency analysis
# 006382.python.hook-matplotlib.line31.comment in contemporary PyInstaller versions, we also need to collect the load-order file. This used to be required for
# 006383.python.hook-matplotlib.line32.comment python <= 3.7 (that lacked `os.add_dll_directory`), but is also needed for Anaconda python 3.8 and 3.9, where
# 006384.python.hook-matplotlib.line33.comment `delvewheel` falls back to load-order file codepath due to Anaconda breaking `os.add_dll_directory` implementation.
if compat.is_win and hookutils.check_requirement('matplotlib >= 3.7.0'):
    delvewheel_datas, delvewheel_binaries = hookutils.collect_delvewheel_libs_directory('matplotlib')

    datas += delvewheel_datas
    binaries += delvewheel_binaries
