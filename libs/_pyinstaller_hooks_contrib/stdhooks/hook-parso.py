# 015220.python.hook-parso.line1.comment -----------------------------------------------------------------------------
# 015221.python.hook-parso.line2.comment Copyright (c) 2013-2018, PyInstaller Development Team.
# 015222.python.hook-parso.line3.comment
# 015223.python.hook-parso.line4.comment This file is distributed under the terms of the GNU General Public
# 015224.python.hook-parso.line5.comment License (version 2.0 or later).
# 015225.python.hook-parso.line6.comment
# 015226.python.hook-parso.line7.comment The full license is available in LICENSE, distributed with
# 015227.python.hook-parso.line8.comment this software.
# 015228.python.hook-parso.line9.comment
# 015229.python.hook-parso.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015230.python.hook-parso.line11.comment -----------------------------------------------------------------------------

# 015231.python.hook-parso.line13.comment Hook for Parso, a static analysis tool https://pypi.org/project/jedi/ (IPython dependency)

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('parso')
