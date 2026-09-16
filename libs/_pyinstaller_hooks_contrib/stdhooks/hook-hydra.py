# 013916.python.hook-hydra.line1.comment ------------------------------------------------------------------
# 013917.python.hook-hydra.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 013918.python.hook-hydra.line3.comment
# 013919.python.hook-hydra.line4.comment This file is distributed under the terms of the GNU General Public
# 013920.python.hook-hydra.line5.comment License (version 2.0 or later).
# 013921.python.hook-hydra.line6.comment
# 013922.python.hook-hydra.line7.comment The full license is available in LICENSE, distributed with
# 013923.python.hook-hydra.line8.comment this software.
# 013924.python.hook-hydra.line9.comment
# 013925.python.hook-hydra.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013926.python.hook-hydra.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_py310
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, is_module_satisfies

# 013927.python.hook-hydra.line16.comment Collect core plugins.
hiddenimports = collect_submodules('hydra._internal.core_plugins')

# 013928.python.hook-hydra.line19.comment Hydra's plugin manager (`hydra.core.plugins.Plugins`) uses PEP-302 `find_module` / `load_module`, which has been
# 013929.python.hook-hydra.line20.comment deprecated since python 3.4, and has been removed from PyInstaller's frozen importer in PyInstaller 5.8. For python
# 013930.python.hook-hydra.line21.comment 3.10 and newer, they implemented new codepath that uses `find_spec`, but for earlier python versions, they opted to
# 013931.python.hook-hydra.line22.comment keep using the old codepath.
# 013932.python.hook-hydra.line23.comment
# 013933.python.hook-hydra.line24.comment See: https://github.com/facebookresearch/hydra/pull/2531
# 013934.python.hook-hydra.line25.comment
# 013935.python.hook-hydra.line26.comment To work around the incompatibility with PyInstaller >= 5.8 when using python < 3.10, force collection of plugins as
# 013936.python.hook-hydra.line27.comment source .py files. This way, they end up handled by python's built-in finder/importer instead of PyInstaller's
# 013937.python.hook-hydra.line28.comment frozen importer.
if not is_py310 and is_module_satisfies("PyInstaller >= 5.8"):
    module_collection_mode = {
        'hydra._internal.core_plugins': 'py',
        'hydra_plugins': 'py',
    }

# 013938.python.hook-hydra.line35.comment Collect package's data files, such as default configuration files.
datas = collect_data_files('hydra')
