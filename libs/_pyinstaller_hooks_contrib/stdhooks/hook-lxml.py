# 014453.python.hook-lxml.line1.comment ------------------------------------------------------------------
# 014454.python.hook-lxml.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014455.python.hook-lxml.line3.comment
# 014456.python.hook-lxml.line4.comment This file is distributed under the terms of the GNU General Public
# 014457.python.hook-lxml.line5.comment License (version 2.0 or later).
# 014458.python.hook-lxml.line6.comment
# 014459.python.hook-lxml.line7.comment The full license is available in LICENSE, distributed with
# 014460.python.hook-lxml.line8.comment this software.
# 014461.python.hook-lxml.line9.comment
# 014462.python.hook-lxml.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014463.python.hook-lxml.line11.comment ------------------------------------------------------------------
# 014464.python.hook-lxml.line12.comment
# 014465.python.hook-lxml.line13.comment lxml is not fully embedded when using standard hiddenimports
# 014466.python.hook-lxml.line14.comment see https://github.com/pyinstaller/pyinstaller/issues/5306
# 014467.python.hook-lxml.line15.comment
# 014468.python.hook-lxml.line16.comment Tested with lxml 4.6.1

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('lxml')
