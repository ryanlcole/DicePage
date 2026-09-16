# 006579.python.hook-pygments.line1.comment -----------------------------------------------------------------------------
# 006580.python.hook-pygments.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006581.python.hook-pygments.line3.comment
# 006582.python.hook-pygments.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006583.python.hook-pygments.line5.comment or later) with exception for distributing the bootloader.
# 006584.python.hook-pygments.line6.comment
# 006585.python.hook-pygments.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006586.python.hook-pygments.line8.comment
# 006587.python.hook-pygments.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006588.python.hook-pygments.line10.comment -----------------------------------------------------------------------------
"""
PyInstaller hook file for Pygments. Tested with version 2.0.2.
"""

from PyInstaller.utils.hooks import collect_submodules

# 006589.python.hook-pygments.line17.comment The following applies to pygments version 2.0.2, as reported by ``pip show pygments``.
# 006590.python.hook-pygments.line18.comment
# 006591.python.hook-pygments.line19.comment From pygments.formatters, line 37::
# 006592.python.hook-pygments.line20.comment
# 006593.python.hook-pygments.line21.comment def _load_formatters(module_name):
# 006594.python.hook-pygments.line22.comment """Load a formatter (and all others in the module too)."""
# 006595.python.hook-pygments.line23.comment mod = __import__(module_name, None, None, ['__all__'])
# 006596.python.hook-pygments.line24.comment
# 006597.python.hook-pygments.line25.comment Therefore, we need all the modules in ``pygments.formatters``.

hiddenimports = collect_submodules('pygments.formatters')
hiddenimports.extend(collect_submodules('pygments.lexers'))
hiddenimports.extend(collect_submodules('pygments.styles'))
