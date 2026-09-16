# 016099.python.hook-pyppeteer.line1.comment ------------------------------------------------------------------
# 016100.python.hook-pyppeteer.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016101.python.hook-pyppeteer.line3.comment
# 016102.python.hook-pyppeteer.line4.comment This file is distributed under the terms of the GNU General Public
# 016103.python.hook-pyppeteer.line5.comment License (version 2.0 or later).
# 016104.python.hook-pyppeteer.line6.comment
# 016105.python.hook-pyppeteer.line7.comment The full license is available in LICENSE, distributed with
# 016106.python.hook-pyppeteer.line8.comment this software.
# 016107.python.hook-pyppeteer.line9.comment
# 016108.python.hook-pyppeteer.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016109.python.hook-pyppeteer.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata

# 016110.python.hook-pyppeteer.line15.comment pyppeteer uses importlib.metadata to query its own version.
datas = copy_metadata("pyppeteer")
