# 016717.python.hook-shotgun_api3.line1.comment ------------------------------------------------------------------
# 016718.python.hook-shotgun_api3.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016719.python.hook-shotgun_api3.line3.comment
# 016720.python.hook-shotgun_api3.line4.comment This file is distributed under the terms of the GNU General Public
# 016721.python.hook-shotgun_api3.line5.comment License (version 2.0 or later).
# 016722.python.hook-shotgun_api3.line6.comment
# 016723.python.hook-shotgun_api3.line7.comment The full license is available in LICENSE, distributed with
# 016724.python.hook-shotgun_api3.line8.comment this software.
# 016725.python.hook-shotgun_api3.line9.comment
# 016726.python.hook-shotgun_api3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016727.python.hook-shotgun_api3.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 016728.python.hook-shotgun_api3.line15.comment Shotgun is using "six" to import these and
# 016729.python.hook-shotgun_api3.line16.comment PyInstaller does not seem to catch them correctly.
hiddenimports = ["xmlrpc", "xmlrpc.client"]

# 016730.python.hook-shotgun_api3.line19.comment Collect the following files:
# 016731.python.hook-shotgun_api3.line20.comment /shotgun_api3/lib/httplib2/python2/cacerts.txt
# 016732.python.hook-shotgun_api3.line21.comment /shotgun_api3/lib/httplib2/python3/cacerts.txt
# 016733.python.hook-shotgun_api3.line22.comment /shotgun_api3/lib/certifi/cacert.pem
datas = collect_data_files("shotgun_api3")
