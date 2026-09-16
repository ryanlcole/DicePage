# 012019.python.hook-apscheduler.line1.comment ------------------------------------------------------------------
# 012020.python.hook-apscheduler.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012021.python.hook-apscheduler.line3.comment
# 012022.python.hook-apscheduler.line4.comment This file is distributed under the terms of the GNU General Public
# 012023.python.hook-apscheduler.line5.comment License (version 2.0 or later).
# 012024.python.hook-apscheduler.line6.comment
# 012025.python.hook-apscheduler.line7.comment The full license is available in LICENSE, distributed with
# 012026.python.hook-apscheduler.line8.comment this software.
# 012027.python.hook-apscheduler.line9.comment
# 012028.python.hook-apscheduler.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012029.python.hook-apscheduler.line11.comment ------------------------------------------------------------------
"""
APScheduler uses entry points to dynamically load executors, job
stores and triggers.
This hook was tested against APScheduler 3.6.3.
"""

from PyInstaller.utils.hooks import (collect_submodules, copy_metadata,
                                     is_module_satisfies)

if is_module_satisfies("apscheduler < 4"):
    if is_module_satisfies("pyinstaller >= 4.4"):
        datas = copy_metadata('APScheduler', recursive=True)
    else:
        datas = copy_metadata('APScheduler')

    hiddenimports = collect_submodules('apscheduler')
