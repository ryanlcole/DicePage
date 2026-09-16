# 015710.python.hook-pyexcel.line1.comment ------------------------------------------------------------------
# 015711.python.hook-pyexcel.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015712.python.hook-pyexcel.line3.comment
# 015713.python.hook-pyexcel.line4.comment This file is distributed under the terms of the GNU General Public
# 015714.python.hook-pyexcel.line5.comment License (version 2.0 or later).
# 015715.python.hook-pyexcel.line6.comment
# 015716.python.hook-pyexcel.line7.comment The full license is available in LICENSE, distributed with
# 015717.python.hook-pyexcel.line8.comment this software.
# 015718.python.hook-pyexcel.line9.comment
# 015719.python.hook-pyexcel.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015720.python.hook-pyexcel.line11.comment ------------------------------------------------------------------

# 015721.python.hook-pyexcel.line13.comment This hook was tested with pyexcel 0.5.13:
# 015722.python.hook-pyexcel.line14.comment https://github.com/pyexcel/pyexcel

hiddenimports = [
    'pyexcel.plugins.renderers.sqlalchemy', 'pyexcel.plugins.renderers.django',
    'pyexcel.plugins.renderers.excel', 'pyexcel.plugins.renderers._texttable',
    'pyexcel.plugins.parsers.excel', 'pyexcel.plugins.parsers.sqlalchemy',
    'pyexcel.plugins.sources.http', 'pyexcel.plugins.sources.file_input',
    'pyexcel.plugins.sources.memory_input',
    'pyexcel.plugins.sources.file_output',
    'pyexcel.plugins.sources.output_to_memory',
    'pyexcel.plugins.sources.pydata.bookdict',
    'pyexcel.plugins.sources.pydata.dictsource',
    'pyexcel.plugins.sources.pydata.arraysource',
    'pyexcel.plugins.sources.pydata.records', 'pyexcel.plugins.sources.django',
    'pyexcel.plugins.sources.sqlalchemy', 'pyexcel.plugins.sources.querysets'
]
