# 005473.python.hook-encodings.line1.comment -----------------------------------------------------------------------------
# 005474.python.hook-encodings.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005475.python.hook-encodings.line3.comment
# 005476.python.hook-encodings.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005477.python.hook-encodings.line5.comment or later) with exception for distributing the bootloader.
# 005478.python.hook-encodings.line6.comment
# 005479.python.hook-encodings.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005480.python.hook-encodings.line8.comment
# 005481.python.hook-encodings.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005482.python.hook-encodings.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('encodings')
