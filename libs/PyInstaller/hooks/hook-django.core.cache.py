# 005371.python.hook-django.core.cache.line1.comment -----------------------------------------------------------------------------
# 005372.python.hook-django.core.cache.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005373.python.hook-django.core.cache.line3.comment
# 005374.python.hook-django.core.cache.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005375.python.hook-django.core.cache.line5.comment or later) with exception for distributing the bootloader.
# 005376.python.hook-django.core.cache.line6.comment
# 005377.python.hook-django.core.cache.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005378.python.hook-django.core.cache.line8.comment
# 005379.python.hook-django.core.cache.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005380.python.hook-django.core.cache.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('django.core.cache.backends')
