# 016136.python.hook-pypsexec.line1.comment ------------------------------------------------------------------
# 016137.python.hook-pypsexec.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 016138.python.hook-pypsexec.line3.comment
# 016139.python.hook-pypsexec.line4.comment This file is distributed under the terms of the GNU General Public
# 016140.python.hook-pypsexec.line5.comment License (version 2.0 or later).
# 016141.python.hook-pypsexec.line6.comment
# 016142.python.hook-pypsexec.line7.comment The full license is available in LICENSE, distributed with
# 016143.python.hook-pypsexec.line8.comment this software.
# 016144.python.hook-pypsexec.line9.comment
# 016145.python.hook-pypsexec.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016146.python.hook-pypsexec.line11.comment ------------------------------------------------------------------

# 016147.python.hook-pypsexec.line13.comment The bundled paexec.exe file needs to be collected (as data file; on any platform)
# 016148.python.hook-pypsexec.line14.comment because it is deployed to the remote side during execution.

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pypsexec')
