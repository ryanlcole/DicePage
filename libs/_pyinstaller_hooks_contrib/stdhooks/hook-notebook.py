# 014856.python.hook-notebook.line1.comment ------------------------------------------------------------------
# 014857.python.hook-notebook.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014858.python.hook-notebook.line3.comment
# 014859.python.hook-notebook.line4.comment This file is distributed under the terms of the GNU General Public
# 014860.python.hook-notebook.line5.comment License (version 2.0 or later).
# 014861.python.hook-notebook.line6.comment
# 014862.python.hook-notebook.line7.comment The full license is available in LICENSE, distributed with
# 014863.python.hook-notebook.line8.comment this software.
# 014864.python.hook-notebook.line9.comment
# 014865.python.hook-notebook.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014866.python.hook-notebook.line11.comment ------------------------------------------------------------------

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from jupyter_core.paths import jupyter_config_path, jupyter_path

# 014867.python.hook-notebook.line17.comment collect modules for handlers
hiddenimports = collect_submodules('notebook', filter=lambda name: name.endswith('.handles'))
hiddenimports.append('notebook.services.shutdown')

datas = collect_data_files('notebook')

# 014868.python.hook-notebook.line23.comment Collect share and etc folder for pre-installed extensions
datas += [(path, 'share/jupyter')
          for path in jupyter_path() if os.path.exists(path)]
datas += [(path, 'etc/jupyter')
          for path in jupyter_config_path() if os.path.exists(path)]
