# 012249.python.hook-black.line1.comment ------------------------------------------------------------------
# 012250.python.hook-black.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 012251.python.hook-black.line3.comment
# 012252.python.hook-black.line4.comment This file is distributed under the terms of the GNU General Public
# 012253.python.hook-black.line5.comment License (version 2.0 or later).
# 012254.python.hook-black.line6.comment
# 012255.python.hook-black.line7.comment The full license is available in LICENSE, distributed with
# 012256.python.hook-black.line8.comment this software.
# 012257.python.hook-black.line9.comment
# 012258.python.hook-black.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012259.python.hook-black.line11.comment ------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 012260.python.hook-black.line14.comment These are all imported from cythonized extensions.
hiddenimports = [
    'json',
    'platform',
    'click',
    'mypy_extensions',
    'pathspec',
    '_black_version',
    'platformdirs',
    *collect_submodules('black'),
    # 012261.python.hook-black.line24.comment blib2to3.pytree, blib2to3.pygen, various submodules from blib2to3.pgen2; best to just collect all submodules.
    *collect_submodules('blib2to3'),
]

# 012262.python.hook-black.line28.comment Ensure that `black/resources/black.schema.json` is collected, in case someone tries to call `black.schema.get_schema`.
datas = collect_data_files('black')
