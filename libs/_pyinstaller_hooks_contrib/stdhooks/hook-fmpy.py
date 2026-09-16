# 013455.python.hook-fmpy.line1.comment ------------------------------------------------------------------
# 013456.python.hook-fmpy.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013457.python.hook-fmpy.line3.comment
# 013458.python.hook-fmpy.line4.comment This file is distributed under the terms of the GNU General Public
# 013459.python.hook-fmpy.line5.comment License (version 2.0 or later).
# 013460.python.hook-fmpy.line6.comment
# 013461.python.hook-fmpy.line7.comment The full license is available in LICENSE, distributed with
# 013462.python.hook-fmpy.line8.comment this software.
# 013463.python.hook-fmpy.line9.comment
# 013464.python.hook-fmpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013465.python.hook-fmpy.line11.comment ------------------------------------------------------------------
"""
Hook for FMPy, a library to simulate Functional Mockup Units (FMUs)
https://github.com/CATIA-Systems/FMPy

Adds the data files that are required at runtime:

- XSD schema files
- dynamic libraries for the CVode solver
- source and header files for the compilation of c-code FMUs
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('fmpy')
