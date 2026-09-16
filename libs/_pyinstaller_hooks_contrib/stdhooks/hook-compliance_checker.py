# 012600.python.hook-compliance_checker.line1.comment ------------------------------------------------------------------
# 012601.python.hook-compliance_checker.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 012602.python.hook-compliance_checker.line3.comment
# 012603.python.hook-compliance_checker.line4.comment This file is distributed under the terms of the GNU General Public
# 012604.python.hook-compliance_checker.line5.comment License (version 2.0 or later).
# 012605.python.hook-compliance_checker.line6.comment
# 012606.python.hook-compliance_checker.line7.comment The full license is available in LICENSE, distributed with
# 012607.python.hook-compliance_checker.line8.comment this software.
# 012608.python.hook-compliance_checker.line9.comment
# 012609.python.hook-compliance_checker.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012610.python.hook-compliance_checker.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, copy_metadata, collect_data_files

# 012611.python.hook-compliance_checker.line15.comment Collect submodules to ensure that checker plugins are collected. but avoid collecting tests sub-package.
hiddenimports = collect_submodules('compliance_checker', filter=lambda name: name != 'compliance_checker.tests')

# 012612.python.hook-compliance_checker.line18.comment Copy metadata, because checker plugins are discovered via entry-points
datas = copy_metadata('compliance_checker')

# 012613.python.hook-compliance_checker.line21.comment Include data files from compliance_checker/data sub-directory.
datas += collect_data_files('compliance_checker', includes=['data/**'])
