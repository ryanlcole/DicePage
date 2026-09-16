# 017752.python.hook-torchvision.line1.comment ------------------------------------------------------------------
# 017753.python.hook-torchvision.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017754.python.hook-torchvision.line3.comment
# 017755.python.hook-torchvision.line4.comment This file is distributed under the terms of the GNU General Public
# 017756.python.hook-torchvision.line5.comment License (version 2.0 or later).
# 017757.python.hook-torchvision.line6.comment
# 017758.python.hook-torchvision.line7.comment The full license is available in LICENSE, distributed with
# 017759.python.hook-torchvision.line8.comment this software.
# 017760.python.hook-torchvision.line9.comment
# 017761.python.hook-torchvision.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017762.python.hook-torchvision.line11.comment ------------------------------------------------------------------

# 017763.python.hook-torchvision.line13.comment Functions from torchvision.ops.* modules require torchvision._C extension module, which PyInstaller fails to pick up
# 017764.python.hook-torchvision.line14.comment automatically due to indirect load.
hiddenimports = ['torchvision._C']

# 017765.python.hook-torchvision.line17.comment Collect source .py files for JIT/torchscript. Requires PyInstaller >= 5.3, no-op in older versions.
module_collection_mode = 'pyz+py'
