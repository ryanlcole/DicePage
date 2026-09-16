# 014548.python.hook-metpy.line1.comment ------------------------------------------------------------------
# 014549.python.hook-metpy.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 014550.python.hook-metpy.line3.comment
# 014551.python.hook-metpy.line4.comment This file is distributed under the terms of the GNU General Public
# 014552.python.hook-metpy.line5.comment License (version 2.0 or later).
# 014553.python.hook-metpy.line6.comment
# 014554.python.hook-metpy.line7.comment The full license is available in LICENSE, distributed with
# 014555.python.hook-metpy.line8.comment this software.
# 014556.python.hook-metpy.line9.comment
# 014557.python.hook-metpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014558.python.hook-metpy.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# 014559.python.hook-metpy.line15.comment MetPy requires metadata, because it queries its version via
# 014560.python.hook-metpy.line16.comment pkg_resources.get_distribution(__package__).version or, in newer
# 014561.python.hook-metpy.line17.comment versions, importlib.metadata.version(__package__)
datas = copy_metadata('metpy')

# 014562.python.hook-metpy.line20.comment Collect data files
datas += collect_data_files('metpy')
