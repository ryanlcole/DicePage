# 017865.python.hook-trame_keycloak.line1.comment ------------------------------------------------------------------
# 017866.python.hook-trame_keycloak.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017867.python.hook-trame_keycloak.line3.comment
# 017868.python.hook-trame_keycloak.line4.comment This file is distributed under the terms of the GNU General Public
# 017869.python.hook-trame_keycloak.line5.comment License (version 2.0 or later).
# 017870.python.hook-trame_keycloak.line6.comment
# 017871.python.hook-trame_keycloak.line7.comment The full license is available in LICENSE, distributed with
# 017872.python.hook-trame_keycloak.line8.comment this software.
# 017873.python.hook-trame_keycloak.line9.comment
# 017874.python.hook-trame_keycloak.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017875.python.hook-trame_keycloak.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_keycloak", subdir="module")
