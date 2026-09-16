# 012052.python.hook-astroid.line1.comment ------------------------------------------------------------------
# 012053.python.hook-astroid.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012054.python.hook-astroid.line3.comment
# 012055.python.hook-astroid.line4.comment This file is distributed under the terms of the GNU General Public
# 012056.python.hook-astroid.line5.comment License (version 2.0 or later).
# 012057.python.hook-astroid.line6.comment
# 012058.python.hook-astroid.line7.comment The full license is available in LICENSE, distributed with
# 012059.python.hook-astroid.line8.comment this software.
# 012060.python.hook-astroid.line9.comment
# 012061.python.hook-astroid.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012062.python.hook-astroid.line11.comment ------------------------------------------------------------------
# 012063.python.hook-astroid.line12.comment
# 012064.python.hook-astroid.line13.comment ***************************************************
# 012065.python.hook-astroid.line14.comment hook-astriod.py - PyInstaller hook file for astriod
# 012066.python.hook-astroid.line15.comment ***************************************************
# 012067.python.hook-astroid.line16.comment The astriod package, in __pkginfo__.py, is version 1.1.1. Looking at its
# 012068.python.hook-astroid.line17.comment source:
# 012069.python.hook-astroid.line18.comment
# 012070.python.hook-astroid.line19.comment From __init__.py, starting at line 111::
# 012071.python.hook-astroid.line20.comment
# 012072.python.hook-astroid.line21.comment BRAIN_MODULES_DIR = join(dirname(__file__), 'brain')
# 012073.python.hook-astroid.line22.comment if BRAIN_MODULES_DIR not in sys.path:
# 012074.python.hook-astroid.line23.comment # add it to the end of the list so user path take precedence
# 012075.python.hook-astroid.line24.comment sys.path.append(BRAIN_MODULES_DIR)
# 012076.python.hook-astroid.line25.comment # load modules in this directory
# 012077.python.hook-astroid.line26.comment for module in listdir(BRAIN_MODULES_DIR):
# 012078.python.hook-astroid.line27.comment if module.endswith('.py'):
# 012079.python.hook-astroid.line28.comment __import__(module[:-3])
# 012080.python.hook-astroid.line29.comment
# 012081.python.hook-astroid.line30.comment So, we need all the Python source in the ``brain/`` subdirectory,
# 012082.python.hook-astroid.line31.comment since this is run-time discovered and loaded. Therefore, these
# 012083.python.hook-astroid.line32.comment files are all data files.

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, \
    is_module_or_submodule

# 012084.python.hook-astroid.line37.comment Note that brain/ isn't a module (it lacks an __init__.py, so it can't be
# 012085.python.hook-astroid.line38.comment referred to as astroid.brain; instead, locate it as package astriod,
# 012086.python.hook-astroid.line39.comment subdirectory brain/.
datas = collect_data_files('astroid', True, 'brain')

# 012087.python.hook-astroid.line42.comment Update: in astroid v 1.4.1, the brain/ module import parts of astroid. Since
# 012088.python.hook-astroid.line43.comment everything in brain/ is dynamically imported, these are hidden imports. For
# 012089.python.hook-astroid.line44.comment simplicity, include everything in astroid. Exclude all the test/ subpackage
# 012090.python.hook-astroid.line45.comment contents and the test_util module.
hiddenimports = ['six'] + collect_submodules('astroid',
                                             lambda name: (not is_module_or_submodule(name, 'astroid.tests')) and
                                             (not name == 'test_util'))
