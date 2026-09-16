# 017264.python.hook-sspilib.raw.line1.comment ------------------------------------------------------------------
# 017265.python.hook-sspilib.raw.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 017266.python.hook-sspilib.raw.line3.comment
# 017267.python.hook-sspilib.raw.line4.comment This file is distributed under the terms of the GNU General Public
# 017268.python.hook-sspilib.raw.line5.comment License (version 2.0 or later).
# 017269.python.hook-sspilib.raw.line6.comment
# 017270.python.hook-sspilib.raw.line7.comment The full license is available in LICENSE, distributed with
# 017271.python.hook-sspilib.raw.line8.comment this software.
# 017272.python.hook-sspilib.raw.line9.comment
# 017273.python.hook-sspilib.raw.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017274.python.hook-sspilib.raw.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 017275.python.hook-sspilib.raw.line15.comment This seems to be required in python <= 3.9; in later versions, the `dataclasses` module ends up included via a
# 017276.python.hook-sspilib.raw.line16.comment different import chain. But for the sake of consistency, keep the hiddenimport for all python versions.
hiddenimports = ['dataclasses']

# 017277.python.hook-sspilib.raw.line19.comment Collect submodules of `sspilib.raw` - most of which are cythonized extensions.
hiddenimports += collect_submodules('sspilib.raw')
