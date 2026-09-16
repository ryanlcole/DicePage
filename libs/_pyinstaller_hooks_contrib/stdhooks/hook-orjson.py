# 015131.python.hook-orjson.line1.comment ------------------------------------------------------------------
# 015132.python.hook-orjson.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 015133.python.hook-orjson.line3.comment
# 015134.python.hook-orjson.line4.comment This file is distributed under the terms of the GNU General Public
# 015135.python.hook-orjson.line5.comment License (version 2.0 or later).
# 015136.python.hook-orjson.line6.comment
# 015137.python.hook-orjson.line7.comment The full license is available in LICENSE, distributed with
# 015138.python.hook-orjson.line8.comment this software.
# 015139.python.hook-orjson.line9.comment
# 015140.python.hook-orjson.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015141.python.hook-orjson.line11.comment ------------------------------------------------------------------

# 015142.python.hook-orjson.line13.comment Forced import of these modules happens on first orjson import
# 015143.python.hook-orjson.line14.comment and orjson is a compiled extension module.
hiddenimports = [
    'uuid',
    'zoneinfo',
    'enum',
    'json',
    'dataclasses',
]
