# 005361.python.hook-django.contrib.sessions.line1.comment -----------------------------------------------------------------------------
# 005362.python.hook-django.contrib.sessions.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005363.python.hook-django.contrib.sessions.line3.comment
# 005364.python.hook-django.contrib.sessions.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005365.python.hook-django.contrib.sessions.line5.comment or later) with exception for distributing the bootloader.
# 005366.python.hook-django.contrib.sessions.line6.comment
# 005367.python.hook-django.contrib.sessions.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005368.python.hook-django.contrib.sessions.line8.comment
# 005369.python.hook-django.contrib.sessions.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005370.python.hook-django.contrib.sessions.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('django.contrib.sessions.backends')
