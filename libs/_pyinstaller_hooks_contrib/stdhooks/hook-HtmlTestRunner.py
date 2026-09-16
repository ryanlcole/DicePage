# 011783.python.hook-HtmlTestRunner.line1.comment ------------------------------------------------------------------
# 011784.python.hook-HtmlTestRunner.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011785.python.hook-HtmlTestRunner.line3.comment
# 011786.python.hook-HtmlTestRunner.line4.comment This file is distributed under the terms of the GNU General Public
# 011787.python.hook-HtmlTestRunner.line5.comment License (version 2.0 or later).
# 011788.python.hook-HtmlTestRunner.line6.comment
# 011789.python.hook-HtmlTestRunner.line7.comment The full license is available in LICENSE, distributed with
# 011790.python.hook-HtmlTestRunner.line8.comment this software.
# 011791.python.hook-HtmlTestRunner.line9.comment
# 011792.python.hook-HtmlTestRunner.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011793.python.hook-HtmlTestRunner.line11.comment ------------------------------------------------------------------

# 011794.python.hook-HtmlTestRunner.line13.comment Hook for HtmlTestRunner: https://pypi.org/project/html-testRunner//1.2.1

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('HtmlTestRunner')
