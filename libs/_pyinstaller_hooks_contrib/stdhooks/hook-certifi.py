# 012479.python.hook-certifi.line1.comment ------------------------------------------------------------------
# 012480.python.hook-certifi.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012481.python.hook-certifi.line3.comment
# 012482.python.hook-certifi.line4.comment This file is distributed under the terms of the GNU General Public
# 012483.python.hook-certifi.line5.comment License (version 2.0 or later).
# 012484.python.hook-certifi.line6.comment
# 012485.python.hook-certifi.line7.comment The full license is available in LICENSE, distributed with
# 012486.python.hook-certifi.line8.comment this software.
# 012487.python.hook-certifi.line9.comment
# 012488.python.hook-certifi.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012489.python.hook-certifi.line11.comment ------------------------------------------------------------------

# 012490.python.hook-certifi.line13.comment Certifi is a carefully curated collection of Root Certificates for
# 012491.python.hook-certifi.line14.comment validating the trustworthiness of SSL certificates while verifying
# 012492.python.hook-certifi.line15.comment the identity of TLS hosts.

# 012493.python.hook-certifi.line17.comment It has been extracted from the Requests project.

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('certifi')
