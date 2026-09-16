# 012275.python.hook-blib2to3.line1.comment ------------------------------------------------------------------
# 012276.python.hook-blib2to3.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 012277.python.hook-blib2to3.line3.comment
# 012278.python.hook-blib2to3.line4.comment This file is distributed under the terms of the GNU General Public
# 012279.python.hook-blib2to3.line5.comment License (version 2.0 or later).
# 012280.python.hook-blib2to3.line6.comment
# 012281.python.hook-blib2to3.line7.comment The full license is available in LICENSE, distributed with
# 012282.python.hook-blib2to3.line8.comment this software.
# 012283.python.hook-blib2to3.line9.comment
# 012284.python.hook-blib2to3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012285.python.hook-blib2to3.line11.comment ------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from _pyinstaller_hooks_contrib.compat import importlib_metadata


# 012286.python.hook-blib2to3.line16.comment Find the mypyc extension module for `black`, which is called something like `30fcd23745efe32ce681__mypyc`. The prefix
# 012287.python.hook-blib2to3.line17.comment changes with each `black` version, so we need to obtain the name by looking at distribution's list of files.
def _find_mypyc_module():
    try:
        dist = importlib_metadata.distribution("black")
    except importlib_metadata.PackageNotFoundError:
        return []
    return [entry.name.split('.')[0] for entry in (dist.files or []) if '__mypyc' in entry.name]


hiddenimports = [
    *_find_mypyc_module(),
    'dataclasses',
    'pkgutil',
    'tempfile',
    *collect_submodules('blib2to3')
]

# 012288.python.hook-blib2to3.line34.comment Ensure that data files, such as `PatternGrammar.txt` and `Grammar.txt`, are collected.
datas = collect_data_files('blib2to3')
