# 003060.python.hook-PyQt5.Qt.line1.comment -----------------------------------------------------------------------------
# 003061.python.hook-PyQt5.Qt.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003062.python.hook-PyQt5.Qt.line3.comment
# 003063.python.hook-PyQt5.Qt.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003064.python.hook-PyQt5.Qt.line5.comment or later) with exception for distributing the bootloader.
# 003065.python.hook-PyQt5.Qt.line6.comment
# 003066.python.hook-PyQt5.Qt.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003067.python.hook-PyQt5.Qt.line8.comment
# 003068.python.hook-PyQt5.Qt.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003069.python.hook-PyQt5.Qt.line10.comment -----------------------------------------------------------------------------

# 003070.python.hook-PyQt5.Qt.line12.comment When PyQt5.Qt is imported it implies the import of all PyQt5 modules. See
# 003071.python.hook-PyQt5.Qt.line13.comment http://pyqt.sourceforge.net/Docs/PyQt5/Qt.html.
import os

from PyInstaller.utils.hooks import get_module_file_attribute

# 003072.python.hook-PyQt5.Qt.line18.comment Only do this if PyQt5 is found.
mfi = get_module_file_attribute('PyQt5')
if mfi:
    # 003073.python.hook-PyQt5.Qt.line21.comment Determine the name of all these modules by looking in the PyQt5 directory.
    hiddenimports = []
    for f in os.listdir(os.path.dirname(mfi)):
        root, ext = os.path.splitext(os.path.basename(f))
        if root.startswith('Qt') and root != 'Qt':
            # 003074.python.hook-PyQt5.Qt.line26.comment On Linux and macOS, PyQt 5.14.1 has a ``.abi3`` suffix on all library names. Remove it.
            if root.endswith('.abi3'):
                root = root[:-5]
            hiddenimports.append('PyQt5.' + root)
