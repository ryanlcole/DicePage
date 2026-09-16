# 016663.python.hook-setuptools_scm.line1.comment ------------------------------------------------------------------
# 016664.python.hook-setuptools_scm.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 016665.python.hook-setuptools_scm.line3.comment
# 016666.python.hook-setuptools_scm.line4.comment This file is distributed under the terms of the GNU General Public
# 016667.python.hook-setuptools_scm.line5.comment License (version 2.0 or later).
# 016668.python.hook-setuptools_scm.line6.comment
# 016669.python.hook-setuptools_scm.line7.comment The full license is available in LICENSE, distributed with
# 016670.python.hook-setuptools_scm.line8.comment this software.
# 016671.python.hook-setuptools_scm.line9.comment
# 016672.python.hook-setuptools_scm.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016673.python.hook-setuptools_scm.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata

# 016674.python.hook-setuptools_scm.line15.comment Ensure `metadata of setuptools` dist is collected, to avoid run-time warning about unknown/incompatible `setuptools`
# 016675.python.hook-setuptools_scm.line16.comment version.
datas = copy_metadata('setuptools')
