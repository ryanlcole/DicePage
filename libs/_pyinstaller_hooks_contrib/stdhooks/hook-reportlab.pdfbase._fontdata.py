# 016463.python.hook-reportlab.pdfbase._fontdata.line1.comment ------------------------------------------------------------------
# 016464.python.hook-reportlab.pdfbase._fontdata.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016465.python.hook-reportlab.pdfbase._fontdata.line3.comment
# 016466.python.hook-reportlab.pdfbase._fontdata.line4.comment This file is distributed under the terms of the GNU General Public
# 016467.python.hook-reportlab.pdfbase._fontdata.line5.comment License (version 2.0 or later).
# 016468.python.hook-reportlab.pdfbase._fontdata.line6.comment
# 016469.python.hook-reportlab.pdfbase._fontdata.line7.comment The full license is available in LICENSE, distributed with
# 016470.python.hook-reportlab.pdfbase._fontdata.line8.comment this software.
# 016471.python.hook-reportlab.pdfbase._fontdata.line9.comment
# 016472.python.hook-reportlab.pdfbase._fontdata.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016473.python.hook-reportlab.pdfbase._fontdata.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 016474.python.hook-reportlab.pdfbase._fontdata.line15.comment Tested on Windows 7 x64 with Python 2.7.6 x32 using ReportLab 3.0
# 016475.python.hook-reportlab.pdfbase._fontdata.line16.comment This has been observed to *not* work on ReportLab 2.7
hiddenimports = collect_submodules('reportlab.pdfbase',
                                   lambda name: name.startswith('reportlab.pdfbase._fontdata_'))
