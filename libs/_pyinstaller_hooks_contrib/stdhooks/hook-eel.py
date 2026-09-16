# 013086.python.hook-eel.line1.comment ------------------------------------------------------------------
# 013087.python.hook-eel.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013088.python.hook-eel.line3.comment
# 013089.python.hook-eel.line4.comment This file is distributed under the terms of the GNU General Public
# 013090.python.hook-eel.line5.comment License (version 2.0 or later).
# 013091.python.hook-eel.line6.comment
# 013092.python.hook-eel.line7.comment The full license is available in LICENSE, distributed with
# 013093.python.hook-eel.line8.comment this software.
# 013094.python.hook-eel.line9.comment
# 013095.python.hook-eel.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013096.python.hook-eel.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('eel')
hiddenimports = ['bottle_websocket']
