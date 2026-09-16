# 013905.python.hook-humanize.line1.comment ------------------------------------------------------------------
# 013906.python.hook-humanize.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013907.python.hook-humanize.line3.comment
# 013908.python.hook-humanize.line4.comment This file is distributed under the terms of the GNU General Public
# 013909.python.hook-humanize.line5.comment License (version 2.0 or later).
# 013910.python.hook-humanize.line6.comment
# 013911.python.hook-humanize.line7.comment The full license is available in LICENSE, distributed with
# 013912.python.hook-humanize.line8.comment this software.
# 013913.python.hook-humanize.line9.comment
# 013914.python.hook-humanize.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013915.python.hook-humanize.line11.comment ------------------------------------------------------------------
"""
This modest package contains various common humanization utilities, like turning a number into a fuzzy human
readable duration ("3 minutes ago") or into a human readable size or throughput.

https://pypi.org/project/humanize

This hook was tested against humanize 3.5.0.
"""

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('humanize')
