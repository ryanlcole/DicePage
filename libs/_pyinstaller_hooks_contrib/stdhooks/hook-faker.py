# 013317.python.hook-faker.line1.comment ------------------------------------------------------------------
# 013318.python.hook-faker.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013319.python.hook-faker.line3.comment
# 013320.python.hook-faker.line4.comment This file is distributed under the terms of the GNU General Public
# 013321.python.hook-faker.line5.comment License (version 2.0 or later).
# 013322.python.hook-faker.line6.comment
# 013323.python.hook-faker.line7.comment The full license is available in LICENSE, distributed with
# 013324.python.hook-faker.line8.comment this software.
# 013325.python.hook-faker.line9.comment
# 013326.python.hook-faker.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013327.python.hook-faker.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('faker.providers')
datas = (
    collect_data_files('text_unidecode') +  # noqa: W504
    collect_data_files('faker.providers', include_py_files=True)
)
