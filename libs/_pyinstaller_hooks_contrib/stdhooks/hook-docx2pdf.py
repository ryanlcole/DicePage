# 013036.python.hook-docx2pdf.line1.comment ------------------------------------------------------------------
# 013037.python.hook-docx2pdf.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 013038.python.hook-docx2pdf.line3.comment
# 013039.python.hook-docx2pdf.line4.comment This file is distributed under the terms of the GNU General Public
# 013040.python.hook-docx2pdf.line5.comment License (version 2.0 or later).
# 013041.python.hook-docx2pdf.line6.comment
# 013042.python.hook-docx2pdf.line7.comment The full license is available in LICENSE, distributed with
# 013043.python.hook-docx2pdf.line8.comment this software.
# 013044.python.hook-docx2pdf.line9.comment
# 013045.python.hook-docx2pdf.line10.comment SPDX-License-Identifier: GPL-2.0-or-later.
# 013046.python.hook-docx2pdf.line11.comment ------------------------------------------------------------------

# 013047.python.hook-docx2pdf.line13.comment Hook for docx2pdf: https://pypi.org/project/docx2pdf/

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = copy_metadata('docx2pdf')
datas += collect_data_files('docx2pdf')
