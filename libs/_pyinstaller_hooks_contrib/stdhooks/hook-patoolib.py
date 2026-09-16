# 015258.python.hook-patoolib.line1.comment -----------------------------------------------------------------------------
# 015259.python.hook-patoolib.line2.comment Copyright (c) 2017-2024, PyInstaller Development Team.
# 015260.python.hook-patoolib.line3.comment
# 015261.python.hook-patoolib.line4.comment This file is distributed under the terms of the GNU General Public
# 015262.python.hook-patoolib.line5.comment License (version 2.0 or later).
# 015263.python.hook-patoolib.line6.comment
# 015264.python.hook-patoolib.line7.comment The full license is available in LICENSE, distributed with
# 015265.python.hook-patoolib.line8.comment this software.
# 015266.python.hook-patoolib.line9.comment
# 015267.python.hook-patoolib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015268.python.hook-patoolib.line11.comment -----------------------------------------------------------------------------


"""
patoolib uses importlib and pyinstaller doesn't find it and add it to the list of needed modules
"""

from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('patoolib.programs')
