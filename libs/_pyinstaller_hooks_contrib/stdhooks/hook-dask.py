# 012869.python.hook-dask.line1.comment -----------------------------------------------------------------------------
# 012870.python.hook-dask.line2.comment Copyright (c) 2005-2020, PyInstaller Development Team.
# 012871.python.hook-dask.line3.comment
# 012872.python.hook-dask.line4.comment This file is distributed under the terms of the GNU General Public
# 012873.python.hook-dask.line5.comment License (version 2.0 or later).
# 012874.python.hook-dask.line6.comment
# 012875.python.hook-dask.line7.comment The full license is available in LICENSE, distributed with
# 012876.python.hook-dask.line8.comment this software.
# 012877.python.hook-dask.line9.comment
# 012878.python.hook-dask.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012879.python.hook-dask.line11.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 012880.python.hook-dask.line15.comment Collect data files:
# 012881.python.hook-dask.line16.comment - dask.yaml
# 012882.python.hook-dask.line17.comment - dask-schema.yaml
# 012883.python.hook-dask.line18.comment - widgets/templates/*.html.j2 (but avoid collecting files from `widgets/tests/templates`!)
datas = collect_data_files('dask', includes=['*.yml', '*.yaml', 'widgets/templates/*.html.j2'])
