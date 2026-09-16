# 012177.python.hook-backports.line1.comment ------------------------------------------------------------------
# 012178.python.hook-backports.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 012179.python.hook-backports.line3.comment
# 012180.python.hook-backports.line4.comment This file is distributed under the terms of the GNU General Public
# 012181.python.hook-backports.line5.comment License (version 2.0 or later).
# 012182.python.hook-backports.line6.comment
# 012183.python.hook-backports.line7.comment The full license is available in LICENSE, distributed with
# 012184.python.hook-backports.line8.comment this software.
# 012185.python.hook-backports.line9.comment
# 012186.python.hook-backports.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012187.python.hook-backports.line11.comment ------------------------------------------------------------------

# 012188.python.hook-backports.line13.comment Some of jaraco's backports packages (backports.functools-lru-cache, backports.tarfile) use pkgutil-style `backports`
# 012189.python.hook-backports.line14.comment namespace package, with `__init__.py` file that contains:
# 012190.python.hook-backports.line15.comment
# 012191.python.hook-backports.line16.comment __path__ = __import__('pkgutil').extend_path(__path__, __name__)
# 012192.python.hook-backports.line17.comment
# 012193.python.hook-backports.line18.comment This import via `__import__` function slips past PyInstaller's modulegraph analysis; so add a hidden import, in case
# 012194.python.hook-backports.line19.comment the user's program (and its dependencies) have no other direct imports of `pkgutil`.
hiddenimports = ['pkgutil']
