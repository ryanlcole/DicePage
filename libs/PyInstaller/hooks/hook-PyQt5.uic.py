# 003583.python.hook-PyQt5.uic.line1.comment -----------------------------------------------------------------------------
# 003584.python.hook-PyQt5.uic.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003585.python.hook-PyQt5.uic.line3.comment
# 003586.python.hook-PyQt5.uic.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003587.python.hook-PyQt5.uic.line5.comment or later) with exception for distributing the bootloader.
# 003588.python.hook-PyQt5.uic.line6.comment
# 003589.python.hook-PyQt5.uic.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003590.python.hook-PyQt5.uic.line8.comment
# 003591.python.hook-PyQt5.uic.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003592.python.hook-PyQt5.uic.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 003593.python.hook-PyQt5.uic.line14.comment We need to include modules in PyQt5.uic.widget-plugins, so they can be dynamically loaded by uic. They should be
# 003594.python.hook-PyQt5.uic.line15.comment included as separate (data-like) files, so they can be found by os.listdir and friends. However, as this directory
# 003595.python.hook-PyQt5.uic.line16.comment is not a package, refer to it using the package (PyQt5.uic) followed by the subdirectory name (``widget-plugins/``).
datas = collect_data_files('PyQt5.uic', True, 'widget-plugins')
