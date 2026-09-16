# 020285.python.hook-zarr.line1.comment ------------------------------------------------------------------
# 020286.python.hook-zarr.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 020287.python.hook-zarr.line3.comment
# 020288.python.hook-zarr.line4.comment This file is distributed under the terms of the GNU General Public
# 020289.python.hook-zarr.line5.comment License (version 2.0 or later).
# 020290.python.hook-zarr.line6.comment
# 020291.python.hook-zarr.line7.comment The full license is available in LICENSE, distributed with
# 020292.python.hook-zarr.line8.comment this software.
# 020293.python.hook-zarr.line9.comment
# 020294.python.hook-zarr.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020295.python.hook-zarr.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('zarr')
