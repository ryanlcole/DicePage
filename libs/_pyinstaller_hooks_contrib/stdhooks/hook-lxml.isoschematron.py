# 014430.python.hook-lxml.isoschematron.line1.comment ------------------------------------------------------------------
# 014431.python.hook-lxml.isoschematron.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014432.python.hook-lxml.isoschematron.line3.comment
# 014433.python.hook-lxml.isoschematron.line4.comment This file is distributed under the terms of the GNU General Public
# 014434.python.hook-lxml.isoschematron.line5.comment License (version 2.0 or later).
# 014435.python.hook-lxml.isoschematron.line6.comment
# 014436.python.hook-lxml.isoschematron.line7.comment The full license is available in LICENSE, distributed with
# 014437.python.hook-lxml.isoschematron.line8.comment this software.
# 014438.python.hook-lxml.isoschematron.line9.comment
# 014439.python.hook-lxml.isoschematron.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014440.python.hook-lxml.isoschematron.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files
import os

# 014441.python.hook-lxml.isoschematron.line16.comment Auxiliary data for isoschematron
datas = collect_data_files('lxml', subdir=os.path.join('isoschematron', 'resources'))
