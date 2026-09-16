# 012162.python.hook-azurerm.line1.comment ------------------------------------------------------------------
# 012163.python.hook-azurerm.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012164.python.hook-azurerm.line3.comment
# 012165.python.hook-azurerm.line4.comment This file is distributed under the terms of the GNU General Public
# 012166.python.hook-azurerm.line5.comment License (version 2.0 or later).
# 012167.python.hook-azurerm.line6.comment
# 012168.python.hook-azurerm.line7.comment The full license is available in LICENSE, distributed with
# 012169.python.hook-azurerm.line8.comment this software.
# 012170.python.hook-azurerm.line9.comment
# 012171.python.hook-azurerm.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012172.python.hook-azurerm.line11.comment ------------------------------------------------------------------
# 012173.python.hook-azurerm.line12.comment Azurerm is a lite api to microsoft azure.
# 012174.python.hook-azurerm.line13.comment Azurerm is using pkg_resources internally which is not supported by py-installer.
# 012175.python.hook-azurerm.line14.comment This hook will collect the module metadata.
# 012176.python.hook-azurerm.line15.comment Tested with Azurerm 0.10.0

from PyInstaller.utils.hooks import copy_metadata, is_module_satisfies

if is_module_satisfies("pyinstaller >= 4.4"):
    datas = copy_metadata("azurerm", recursive=True)
else:
    datas = copy_metadata("azurerm")
