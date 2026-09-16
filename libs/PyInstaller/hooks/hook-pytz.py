# 006598.python.hook-pytz.line1.comment -----------------------------------------------------------------------------
# 006599.python.hook-pytz.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006600.python.hook-pytz.line3.comment
# 006601.python.hook-pytz.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006602.python.hook-pytz.line5.comment or later) with exception for distributing the bootloader.
# 006603.python.hook-pytz.line6.comment
# 006604.python.hook-pytz.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006605.python.hook-pytz.line8.comment
# 006606.python.hook-pytz.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006607.python.hook-pytz.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 006608.python.hook-pytz.line14.comment On Linux pytz installed from distribution repository uses zoneinfo from /usr/share/zoneinfo/ and no data files might
# 006609.python.hook-pytz.line15.comment be collected.
datas = collect_data_files('pytz')

# 006610.python.hook-pytz.line18.comment pytz references pkg_resources in a fall-back codepath that should normally not be reached; add an exclude to prevent
# 006611.python.hook-pytz.line19.comment (now deprecated) pkg_resources from being pulled in the frozen application.
excludedimports = ['pkg_resources']
