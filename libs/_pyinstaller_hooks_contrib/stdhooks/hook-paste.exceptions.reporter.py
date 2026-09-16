# 015247.python.hook-paste.exceptions.reporter.line1.comment ------------------------------------------------------------------
# 015248.python.hook-paste.exceptions.reporter.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015249.python.hook-paste.exceptions.reporter.line3.comment
# 015250.python.hook-paste.exceptions.reporter.line4.comment This file is distributed under the terms of the GNU General Public
# 015251.python.hook-paste.exceptions.reporter.line5.comment License (version 2.0 or later).
# 015252.python.hook-paste.exceptions.reporter.line6.comment
# 015253.python.hook-paste.exceptions.reporter.line7.comment The full license is available in LICENSE, distributed with
# 015254.python.hook-paste.exceptions.reporter.line8.comment this software.
# 015255.python.hook-paste.exceptions.reporter.line9.comment
# 015256.python.hook-paste.exceptions.reporter.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015257.python.hook-paste.exceptions.reporter.line11.comment ------------------------------------------------------------------
"""
Some modules use the old-style import: explicitly include
the new module when the old one is referenced.
"""

hiddenimports = ["email.mime.text", "email.mime.multipart"]
