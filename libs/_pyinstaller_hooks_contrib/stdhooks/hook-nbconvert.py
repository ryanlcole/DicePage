# 014742.python.hook-nbconvert.line1.comment ------------------------------------------------------------------
# 014743.python.hook-nbconvert.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014744.python.hook-nbconvert.line3.comment
# 014745.python.hook-nbconvert.line4.comment This file is distributed under the terms of the GNU General Public
# 014746.python.hook-nbconvert.line5.comment License (version 2.0 or later).
# 014747.python.hook-nbconvert.line6.comment
# 014748.python.hook-nbconvert.line7.comment The full license is available in LICENSE, distributed with
# 014749.python.hook-nbconvert.line8.comment this software.
# 014750.python.hook-nbconvert.line9.comment
# 014751.python.hook-nbconvert.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014752.python.hook-nbconvert.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = collect_data_files('nbconvert')

# 014753.python.hook-nbconvert.line17.comment nbconvert uses entrypoints to read nbconvert.exporters from metadata file entry_points.txt.
datas += copy_metadata('nbconvert')
