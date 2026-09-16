# 013014.python.hook-docutils.line1.comment ------------------------------------------------------------------
# 013015.python.hook-docutils.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013016.python.hook-docutils.line3.comment
# 013017.python.hook-docutils.line4.comment This file is distributed under the terms of the GNU General Public
# 013018.python.hook-docutils.line5.comment License (version 2.0 or later).
# 013019.python.hook-docutils.line6.comment
# 013020.python.hook-docutils.line7.comment The full license is available in LICENSE, distributed with
# 013021.python.hook-docutils.line8.comment this software.
# 013022.python.hook-docutils.line9.comment
# 013023.python.hook-docutils.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013024.python.hook-docutils.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (collect_submodules('docutils.languages') +
                 collect_submodules('docutils.writers') +
                 collect_submodules('docutils.parsers.rst.languages') +
                 collect_submodules('docutils.parsers.rst.directives'))
datas = collect_data_files('docutils')
