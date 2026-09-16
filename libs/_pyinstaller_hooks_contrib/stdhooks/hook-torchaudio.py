# 017712.python.hook-torchaudio.line1.comment ------------------------------------------------------------------
# 017713.python.hook-torchaudio.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 017714.python.hook-torchaudio.line3.comment
# 017715.python.hook-torchaudio.line4.comment This file is distributed under the terms of the GNU General Public
# 017716.python.hook-torchaudio.line5.comment License (version 2.0 or later).
# 017717.python.hook-torchaudio.line6.comment
# 017718.python.hook-torchaudio.line7.comment The full license is available in LICENSE, distributed with
# 017719.python.hook-torchaudio.line8.comment this software.
# 017720.python.hook-torchaudio.line9.comment
# 017721.python.hook-torchaudio.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017722.python.hook-torchaudio.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

# 017723.python.hook-torchaudio.line15.comment Collect dynamic extensions from torchaudio/lib - some of them are loaded dynamically, and are thus not automatically
# 017724.python.hook-torchaudio.line16.comment collected.
binaries = collect_dynamic_libs('torchaudio')
hiddenimports = collect_submodules('torchaudio.lib')

# 017725.python.hook-torchaudio.line20.comment Collect source .py files for JIT/torchscript. Requires PyInstaller >= 5.3, no-op in older versions.
module_collection_mode = 'pyz+py'
