# 005391.python.hook-django.core.management.line1.comment -----------------------------------------------------------------------------
# 005392.python.hook-django.core.management.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005393.python.hook-django.core.management.line3.comment
# 005394.python.hook-django.core.management.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005395.python.hook-django.core.management.line5.comment or later) with exception for distributing the bootloader.
# 005396.python.hook-django.core.management.line6.comment
# 005397.python.hook-django.core.management.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005398.python.hook-django.core.management.line8.comment
# 005399.python.hook-django.core.management.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005400.python.hook-django.core.management.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 005401.python.hook-django.core.management.line14.comment Module django.core.management.commands.shell imports IPython, but it introduces many other dependencies that are not
# 005402.python.hook-django.core.management.line15.comment necessary for a simple django project; ignore the IPython module.
excludedimports = ['IPython', 'matplotlib', 'tkinter']

# 005403.python.hook-django.core.management.line18.comment Django requires management modules for the script 'manage.py'.
hiddenimports = collect_submodules('django.core.management.commands')
