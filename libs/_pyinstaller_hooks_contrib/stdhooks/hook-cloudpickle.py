# 012529.python.hook-cloudpickle.line1.comment ------------------------------------------------------------------
# 012530.python.hook-cloudpickle.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 012531.python.hook-cloudpickle.line3.comment
# 012532.python.hook-cloudpickle.line4.comment This file is distributed under the terms of the GNU General Public
# 012533.python.hook-cloudpickle.line5.comment License (version 2.0 or later).
# 012534.python.hook-cloudpickle.line6.comment
# 012535.python.hook-cloudpickle.line7.comment The full license is available in LICENSE, distributed with
# 012536.python.hook-cloudpickle.line8.comment this software.
# 012537.python.hook-cloudpickle.line9.comment
# 012538.python.hook-cloudpickle.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012539.python.hook-cloudpickle.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 012540.python.hook-cloudpickle.line15.comment cloudpickle to 3.0.0 keeps `cloudpickle_fast` module around for backward compatibility with existing pickled data,
# 012541.python.hook-cloudpickle.line16.comment but does not import it directly anymore. Ensure it is collected nevertheless.
if is_module_satisfies("cloudpickle >= 3.0.0"):
    hiddenimports = ["cloudpickle.cloudpickle_fast"]
