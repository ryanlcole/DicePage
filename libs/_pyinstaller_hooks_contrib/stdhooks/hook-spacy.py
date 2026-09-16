# 017205.python.hook-spacy.line1.comment ------------------------------------------------------------------
# 017206.python.hook-spacy.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 017207.python.hook-spacy.line3.comment
# 017208.python.hook-spacy.line4.comment This file is distributed under the terms of the GNU General Public
# 017209.python.hook-spacy.line5.comment License (version 2.0 or later).
# 017210.python.hook-spacy.line6.comment
# 017211.python.hook-spacy.line7.comment The full license is available in LICENSE, distributed with
# 017212.python.hook-spacy.line8.comment this software.
# 017213.python.hook-spacy.line9.comment
# 017214.python.hook-spacy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017215.python.hook-spacy.line11.comment ------------------------------------------------------------------
"""
Spacy contains hidden imports and data files which are needed to import it
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("spacy")
hiddenimports = collect_submodules("spacy")
