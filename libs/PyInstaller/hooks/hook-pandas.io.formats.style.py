# 006486.python.hook-pandas.io.formats.style.line1.comment -----------------------------------------------------------------------------
# 006487.python.hook-pandas.io.formats.style.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 006488.python.hook-pandas.io.formats.style.line3.comment
# 006489.python.hook-pandas.io.formats.style.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006490.python.hook-pandas.io.formats.style.line5.comment or later) with exception for distributing the bootloader.
# 006491.python.hook-pandas.io.formats.style.line6.comment
# 006492.python.hook-pandas.io.formats.style.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006493.python.hook-pandas.io.formats.style.line8.comment
# 006494.python.hook-pandas.io.formats.style.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006495.python.hook-pandas.io.formats.style.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 006496.python.hook-pandas.io.formats.style.line14.comment This module indirectly imports jinja2
hiddenimports = ['jinja2']

# 006497.python.hook-pandas.io.formats.style.line17.comment It also requires template file stored in pandas/io/formats/templates
datas = collect_data_files('pandas.io.formats')
