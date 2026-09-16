# 020173.python.hook-xarray.line1.comment ------------------------------------------------------------------
# 020174.python.hook-xarray.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 020175.python.hook-xarray.line3.comment
# 020176.python.hook-xarray.line4.comment This file is distributed under the terms of the GNU General Public
# 020177.python.hook-xarray.line5.comment License (version 2.0 or later).
# 020178.python.hook-xarray.line6.comment
# 020179.python.hook-xarray.line7.comment The full license is available in LICENSE, distributed with
# 020180.python.hook-xarray.line8.comment this software.
# 020181.python.hook-xarray.line9.comment
# 020182.python.hook-xarray.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020183.python.hook-xarray.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, collect_entry_point

datas = []
hiddenimports = []

# 020184.python.hook-xarray.line18.comment Collect additional backend plugins that are registered via `xarray.backends` entry-point.
ep_datas, ep_hiddenimports = collect_entry_point('xarray.backends')
datas += ep_datas
hiddenimports += ep_hiddenimports

# 020185.python.hook-xarray.line23.comment Similarly, collect chunk manager entry-points.
ep_datas, ep_hiddenimports = collect_entry_point('xarray.chunkmanagers')
datas += ep_datas
hiddenimports += ep_hiddenimports

# 020186.python.hook-xarray.line28.comment `xarray` requires `numpy` metadata due to several calls to its `xarray.core.utils.module_available` with specified
# 020187.python.hook-xarray.line29.comment `minversion` argument, which end up calling `importlib.metadata.version`.
datas += copy_metadata('numpy')
