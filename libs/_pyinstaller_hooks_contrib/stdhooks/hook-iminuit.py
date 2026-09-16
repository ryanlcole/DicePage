# 013978.python.hook-iminuit.line1.comment ------------------------------------------------------------------
# 013979.python.hook-iminuit.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013980.python.hook-iminuit.line3.comment
# 013981.python.hook-iminuit.line4.comment This file is distributed under the terms of the GNU General Public
# 013982.python.hook-iminuit.line5.comment License (version 2.0 or later).
# 013983.python.hook-iminuit.line6.comment
# 013984.python.hook-iminuit.line7.comment The full license is available in LICENSE, distributed with
# 013985.python.hook-iminuit.line8.comment this software.
# 013986.python.hook-iminuit.line9.comment
# 013987.python.hook-iminuit.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013988.python.hook-iminuit.line11.comment ------------------------------------------------------------------

# 013989.python.hook-iminuit.line13.comment add hooks for iminuit: https://github.com/scikit-hep/iminuit

# 013990.python.hook-iminuit.line15.comment iminuit imports subpackages through a cython module which aren't
# 013991.python.hook-iminuit.line16.comment found by default

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []

# 013992.python.hook-iminuit.line22.comment the iminuit package contains tests which aren't needed when distributing
for mod in collect_submodules('iminuit'):
    if not mod.startswith('iminuit.tests'):
        hiddenimports.append(mod)
