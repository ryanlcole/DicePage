# 014016.python.hook-itk.line1.comment ------------------------------------------------------------------
# 014017.python.hook-itk.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 014018.python.hook-itk.line3.comment
# 014019.python.hook-itk.line4.comment This file is distributed under the terms of the GNU General Public
# 014020.python.hook-itk.line5.comment License (version 2.0 or later).
# 014021.python.hook-itk.line6.comment
# 014022.python.hook-itk.line7.comment The full license is available in LICENSE, distributed with
# 014023.python.hook-itk.line8.comment this software.
# 014024.python.hook-itk.line9.comment
# 014025.python.hook-itk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014026.python.hook-itk.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("itk.Configuration")

# 014027.python.hook-itk.line17.comment `itk` requires `itk/Configuration` directory to exist on filesystem; collect source .py files from `itk.Configuration`
# 014028.python.hook-itk.line18.comment as a work-around that ensures the existence of this directory.
module_collection_mode = {
    "itk.Configuration": "pyz+py",
}
