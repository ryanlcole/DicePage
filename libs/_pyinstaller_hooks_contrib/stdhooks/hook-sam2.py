# 016572.python.hook-sam2.line1.comment ------------------------------------------------------------------
# 016573.python.hook-sam2.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 016574.python.hook-sam2.line3.comment
# 016575.python.hook-sam2.line4.comment This file is distributed under the terms of the GNU General Public
# 016576.python.hook-sam2.line5.comment License (version 2.0 or later).
# 016577.python.hook-sam2.line6.comment
# 016578.python.hook-sam2.line7.comment The full license is available in LICENSE, distributed with
# 016579.python.hook-sam2.line8.comment this software.
# 016580.python.hook-sam2.line9.comment
# 016581.python.hook-sam2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016582.python.hook-sam2.line11.comment ------------------------------------------------------------------

# 016583.python.hook-sam2.line13.comment Hook for Segment Anything Model 2 (SAM 2): https://pypi.org/project/sam2

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 016584.python.hook-sam2.line17.comment Collect config .yaml files.
datas = collect_data_files('sam2')

# 016585.python.hook-sam2.line20.comment Ensure that all indirectly-imported modules are collected (e.g., `sam2.modeling.backbones`).
hiddenimports = collect_submodules('sam2')

# 016586.python.hook-sam2.line23.comment Due to use of `torch.script`, we need to collect source .py files for `sam2`. The `sam2/__init__.py` also seems to be
# 016587.python.hook-sam2.line24.comment required by `hydra`. Furthermore, the source-based introspection attempts to load the source of stdlib `enum` module.
# 016588.python.hook-sam2.line25.comment The module collection mode support and run-time discovery of source .py files for modules that are collected into
# 016589.python.hook-sam2.line26.comment `base_library.zip` archive was added in pyinstaller/pyinstaller#8971 (i.e., PyInstaller > 6.11.1).
module_collection_mode = {
    'sam2': 'pyz+py',
    'enum': 'pyz+py',  # requires PyInstaller > 6.11.1; no-op in earlier versions
}
