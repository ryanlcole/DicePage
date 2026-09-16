# 005381.python.hook-django.core.mail.line1.comment -----------------------------------------------------------------------------
# 005382.python.hook-django.core.mail.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005383.python.hook-django.core.mail.line3.comment
# 005384.python.hook-django.core.mail.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005385.python.hook-django.core.mail.line5.comment or later) with exception for distributing the bootloader.
# 005386.python.hook-django.core.mail.line6.comment
# 005387.python.hook-django.core.mail.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005388.python.hook-django.core.mail.line8.comment
# 005389.python.hook-django.core.mail.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005390.python.hook-django.core.mail.line10.comment -----------------------------------------------------------------------------
"""
django.core.mail uses part of the email package.
The problem is: when using runserver with autoreload mode, the thread that checks for changed files triggers further
imports within the email package, because of the LazyImporter in email (used in 2.5 for backward compatibility).
We then need to name those modules as hidden imports, otherwise at runtime the autoreload thread will complain
with a traceback.
"""

hiddenimports = [
    'email.mime.message',
    'email.mime.image',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.audio',
]
