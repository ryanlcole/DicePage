# 004117.python.hook-PyQt6.uic.line1.comment -----------------------------------------------------------------------------
# 004118.python.hook-PyQt6.uic.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004119.python.hook-PyQt6.uic.line3.comment
# 004120.python.hook-PyQt6.uic.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004121.python.hook-PyQt6.uic.line5.comment or later) with exception for distributing the bootloader.
# 004122.python.hook-PyQt6.uic.line6.comment
# 004123.python.hook-PyQt6.uic.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004124.python.hook-PyQt6.uic.line8.comment
# 004125.python.hook-PyQt6.uic.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004126.python.hook-PyQt6.uic.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 004127.python.hook-PyQt6.uic.line14.comment We need to include modules in PyQt6.uic.widget-plugins, so they can be dynamically loaded by uic. They should be
# 004128.python.hook-PyQt6.uic.line15.comment included as separate (data-like) files, so they can be found by os.listdir and friends. However, as this directory
# 004129.python.hook-PyQt6.uic.line16.comment is not a package, refer to it using the package (PyQt6.uic) followed by the subdirectory name (``widget-plugins/``).
datas = collect_data_files('PyQt6.uic', True, 'widget-plugins')
