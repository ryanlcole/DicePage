# 016418.python.hook-rdflib.line1.comment ------------------------------------------------------------------
# 016419.python.hook-rdflib.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016420.python.hook-rdflib.line3.comment
# 016421.python.hook-rdflib.line4.comment This file is distributed under the terms of the GNU General Public
# 016422.python.hook-rdflib.line5.comment License (version 2.0 or later).
# 016423.python.hook-rdflib.line6.comment
# 016424.python.hook-rdflib.line7.comment The full license is available in LICENSE, distributed with
# 016425.python.hook-rdflib.line8.comment this software.
# 016426.python.hook-rdflib.line9.comment
# 016427.python.hook-rdflib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016428.python.hook-rdflib.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('rdflib.plugins')
