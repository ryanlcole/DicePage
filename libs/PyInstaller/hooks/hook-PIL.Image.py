# 002989.python.hook-PIL.Image.line1.comment -----------------------------------------------------------------------------
# 002990.python.hook-PIL.Image.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 002991.python.hook-PIL.Image.line3.comment
# 002992.python.hook-PIL.Image.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 002993.python.hook-PIL.Image.line5.comment or later) with exception for distributing the bootloader.
# 002994.python.hook-PIL.Image.line6.comment
# 002995.python.hook-PIL.Image.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002996.python.hook-PIL.Image.line8.comment
# 002997.python.hook-PIL.Image.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 002998.python.hook-PIL.Image.line10.comment -----------------------------------------------------------------------------

# 002999.python.hook-PIL.Image.line12.comment This hook was tested with Pillow 2.9.0 (Maintained fork of PIL): https://pypi.python.org/pypi/Pillow

from PyInstaller.utils.hooks import collect_submodules

# 003000.python.hook-PIL.Image.line16.comment Include all PIL image plugins - module names containing 'ImagePlugin'. e.g.  PIL.JpegImagePlugin
hiddenimports = collect_submodules('PIL', lambda name: 'ImagePlugin' in name)
