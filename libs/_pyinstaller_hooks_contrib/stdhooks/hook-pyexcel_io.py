# 015723.python.hook-pyexcel_io.line1.comment ------------------------------------------------------------------
# 015724.python.hook-pyexcel_io.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015725.python.hook-pyexcel_io.line3.comment
# 015726.python.hook-pyexcel_io.line4.comment This file is distributed under the terms of the GNU General Public
# 015727.python.hook-pyexcel_io.line5.comment License (version 2.0 or later).
# 015728.python.hook-pyexcel_io.line6.comment
# 015729.python.hook-pyexcel_io.line7.comment The full license is available in LICENSE, distributed with
# 015730.python.hook-pyexcel_io.line8.comment this software.
# 015731.python.hook-pyexcel_io.line9.comment
# 015732.python.hook-pyexcel_io.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015733.python.hook-pyexcel_io.line11.comment ------------------------------------------------------------------

# 015734.python.hook-pyexcel_io.line13.comment This hook was tested with pyexcel-io 0.5.18:
# 015735.python.hook-pyexcel_io.line14.comment https://github.com/pyexcel/pyexcel-io

hiddenimports = [
    'pyexcel_io.readers.csvr', 'pyexcel_io.readers.csvz',
    'pyexcel_io.readers.tsv', 'pyexcel_io.readers.tsvz',
    'pyexcel_io.writers.csvw', 'pyexcel_io.writers.csvz',
    'pyexcel_io.writers.tsv', 'pyexcel_io.writers.tsvz',
    'pyexcel_io.readers.csvz', 'pyexcel_io.readers.tsv',
    'pyexcel_io.readers.tsvz', 'pyexcel_io.database.importers.django',
    'pyexcel_io.database.importers.sqlalchemy',
    'pyexcel_io.database.exporters.django',
    'pyexcel_io.database.exporters.sqlalchemy'
]
