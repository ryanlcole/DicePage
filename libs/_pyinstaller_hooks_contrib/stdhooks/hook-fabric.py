# 013287.python.hook-fabric.line1.comment ------------------------------------------------------------------
# 013288.python.hook-fabric.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 013289.python.hook-fabric.line3.comment
# 013290.python.hook-fabric.line4.comment This file is distributed under the terms of the GNU General Public
# 013291.python.hook-fabric.line5.comment License (version 2.0 or later).
# 013292.python.hook-fabric.line6.comment
# 013293.python.hook-fabric.line7.comment The full license is available in LICENSE, distributed with
# 013294.python.hook-fabric.line8.comment this software.
# 013295.python.hook-fabric.line9.comment
# 013296.python.hook-fabric.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013297.python.hook-fabric.line11.comment ------------------------------------------------------------------
# 013298.python.hook-fabric.line12.comment
# 013299.python.hook-fabric.line13.comment Fabric is a high level Python (2.7, 3.4+) library designed to execute shell commands remotely over SSH,
# 013300.python.hook-fabric.line14.comment yielding useful Python objects in return
# 013301.python.hook-fabric.line15.comment
# 013302.python.hook-fabric.line16.comment https://docs.fabfile.org/en/latest
# 013303.python.hook-fabric.line17.comment
# 013304.python.hook-fabric.line18.comment Tested with fabric 2.6.0

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('fabric')
