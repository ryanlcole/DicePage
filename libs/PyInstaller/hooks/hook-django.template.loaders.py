# 005463.python.hook-django.template.loaders.line1.comment -----------------------------------------------------------------------------
# 005464.python.hook-django.template.loaders.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005465.python.hook-django.template.loaders.line3.comment
# 005466.python.hook-django.template.loaders.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005467.python.hook-django.template.loaders.line5.comment or later) with exception for distributing the bootloader.
# 005468.python.hook-django.template.loaders.line6.comment
# 005469.python.hook-django.template.loaders.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005470.python.hook-django.template.loaders.line8.comment
# 005471.python.hook-django.template.loaders.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005472.python.hook-django.template.loaders.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('django.template.loaders')
