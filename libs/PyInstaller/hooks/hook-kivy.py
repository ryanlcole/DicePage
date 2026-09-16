# 006228.python.hook-kivy.line1.comment -----------------------------------------------------------------------------
# 006229.python.hook-kivy.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 006230.python.hook-kivy.line3.comment
# 006231.python.hook-kivy.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006232.python.hook-kivy.line5.comment or later) with exception for distributing the bootloader.
# 006233.python.hook-kivy.line6.comment
# 006234.python.hook-kivy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006235.python.hook-kivy.line8.comment
# 006236.python.hook-kivy.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006237.python.hook-kivy.line10.comment -----------------------------------------------------------------------------

from PyInstaller import log as logging
from PyInstaller.utils.hooks import check_requirement

if check_requirement('kivy >= 1.9.1'):
    from kivy.tools.packaging.pyinstaller_hooks import (add_dep_paths, get_deps_all, get_factory_modules, kivy_modules)
    from kivy.tools.packaging.pyinstaller_hooks import excludedimports, datas  # noqa: F401

    add_dep_paths()

    hiddenimports = get_deps_all()['hiddenimports']
    hiddenimports = list(set(get_factory_modules() + kivy_modules + hiddenimports))
else:
    logger = logging.getLogger(__name__)
    logger.warning('Hook disabled because of Kivy version < 1.9.1')
