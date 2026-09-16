# 017726.python.hook-torchtext.line1.comment ------------------------------------------------------------------
# 017727.python.hook-torchtext.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 017728.python.hook-torchtext.line3.comment
# 017729.python.hook-torchtext.line4.comment This file is distributed under the terms of the GNU General Public
# 017730.python.hook-torchtext.line5.comment License (version 2.0 or later).
# 017731.python.hook-torchtext.line6.comment
# 017732.python.hook-torchtext.line7.comment The full license is available in LICENSE, distributed with
# 017733.python.hook-torchtext.line8.comment this software.
# 017734.python.hook-torchtext.line9.comment
# 017735.python.hook-torchtext.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017736.python.hook-torchtext.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

# 017737.python.hook-torchtext.line15.comment Collect dynamic extensions from torchtext/lib - some of them are loaded dynamically, and are thus not automatically
# 017738.python.hook-torchtext.line16.comment collected.
binaries = collect_dynamic_libs('torchtext')
hiddenimports = collect_submodules('torchtext.lib')

# 017739.python.hook-torchtext.line20.comment Collect source .py files for JIT/torchscript. Requires PyInstaller >= 5.3, no-op in older versions.
module_collection_mode = 'pyz+py'
