# 015890.python.hook-pylint.line1.comment ------------------------------------------------------------------
# 015891.python.hook-pylint.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015892.python.hook-pylint.line3.comment
# 015893.python.hook-pylint.line4.comment This file is distributed under the terms of the GNU General Public
# 015894.python.hook-pylint.line5.comment License (version 2.0 or later).
# 015895.python.hook-pylint.line6.comment
# 015896.python.hook-pylint.line7.comment The full license is available in LICENSE, distributed with
# 015897.python.hook-pylint.line8.comment this software.
# 015898.python.hook-pylint.line9.comment
# 015899.python.hook-pylint.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015900.python.hook-pylint.line11.comment ------------------------------------------------------------------
# 015901.python.hook-pylint.line12.comment
# 015902.python.hook-pylint.line13.comment *************************************************
# 015903.python.hook-pylint.line14.comment hook-pylint.py - PyInstaller hook file for pylint
# 015904.python.hook-pylint.line15.comment *************************************************
# 015905.python.hook-pylint.line16.comment The pylint package, in __pkginfo__.py, is version 1.4.3. Looking at its
# 015906.python.hook-pylint.line17.comment source:
# 015907.python.hook-pylint.line18.comment
# 015908.python.hook-pylint.line19.comment From checkers/__init__.py, starting at line 122::
# 015909.python.hook-pylint.line20.comment
# 015910.python.hook-pylint.line21.comment def initialize(linter):
# 015911.python.hook-pylint.line22.comment """initialize linter with checkers in this package """
# 015912.python.hook-pylint.line23.comment register_plugins(linter, __path__[0])
# 015913.python.hook-pylint.line24.comment
# 015914.python.hook-pylint.line25.comment From reporters/__init__.py, starting at line 131::
# 015915.python.hook-pylint.line26.comment
# 015916.python.hook-pylint.line27.comment def initialize(linter):
# 015917.python.hook-pylint.line28.comment """initialize linter with reporters in this package """
# 015918.python.hook-pylint.line29.comment utils.register_plugins(linter, __path__[0])
# 015919.python.hook-pylint.line30.comment
# 015920.python.hook-pylint.line31.comment From utils.py, starting at line 881::
# 015921.python.hook-pylint.line32.comment
# 015922.python.hook-pylint.line33.comment def register_plugins(linter, directory):
# 015923.python.hook-pylint.line34.comment """load all module and package in the given directory, looking for a
# 015924.python.hook-pylint.line35.comment 'register' function in each one, used to register pylint checkers
# 015925.python.hook-pylint.line36.comment """
# 015926.python.hook-pylint.line37.comment imported = {}
# 015927.python.hook-pylint.line38.comment for filename in os.listdir(directory):
# 015928.python.hook-pylint.line39.comment base, extension = splitext(filename)
# 015929.python.hook-pylint.line40.comment if base in imported or base == '__pycache__':
# 015930.python.hook-pylint.line41.comment continue
# 015931.python.hook-pylint.line42.comment if extension in PY_EXTS and base != '__init__' or (
# 015932.python.hook-pylint.line43.comment not extension and isdir(join(directory, base))):
# 015933.python.hook-pylint.line44.comment try:
# 015934.python.hook-pylint.line45.comment module = load_module_from_file(join(directory, filename))
# 015935.python.hook-pylint.line46.comment
# 015936.python.hook-pylint.line47.comment
# 015937.python.hook-pylint.line48.comment So, we need all the Python source in the ``checkers/`` and ``reporters/``
# 015938.python.hook-pylint.line49.comment subdirectories, since these are run-time discovered and loaded. Therefore,
# 015939.python.hook-pylint.line50.comment these files are all data files. In addition, since this is a module, the
# 015940.python.hook-pylint.line51.comment pylint/__init__.py file must be included, since submodules must be children of
# 015941.python.hook-pylint.line52.comment a module.

from PyInstaller.utils.hooks import (
    collect_data_files, collect_submodules, is_module_or_submodule, get_module_file_attribute
)

datas = (
    [(get_module_file_attribute('pylint.__init__'), 'pylint')] +
    collect_data_files('pylint.checkers', True) +
    collect_data_files('pylint.reporters', True)
)


# 015942.python.hook-pylint.line65.comment Add imports from dynamically loaded modules, excluding pylint.test
# 015943.python.hook-pylint.line66.comment subpackage (pylint <= 2.3) and pylint.testutils submodule (pylint < 2.7)
# 015944.python.hook-pylint.line67.comment or subpackage (pylint >= 2.7)
def _filter_func(name):
    return (
        not is_module_or_submodule(name, 'pylint.test') and
        not is_module_or_submodule(name, 'pylint.testutils')
    )


hiddenimports = collect_submodules('pylint', _filter_func)
