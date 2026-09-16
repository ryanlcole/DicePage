# 015432.python.hook-psychopy.line1.comment ------------------------------------------------------------------
# 015433.python.hook-psychopy.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015434.python.hook-psychopy.line3.comment
# 015435.python.hook-psychopy.line4.comment This file is distributed under the terms of the GNU General Public
# 015436.python.hook-psychopy.line5.comment License (version 2.0 or later).
# 015437.python.hook-psychopy.line6.comment
# 015438.python.hook-psychopy.line7.comment The full license is available in LICENSE, distributed with
# 015439.python.hook-psychopy.line8.comment this software.
# 015440.python.hook-psychopy.line9.comment
# 015441.python.hook-psychopy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015442.python.hook-psychopy.line11.comment ------------------------------------------------------------------

# 015443.python.hook-psychopy.line13.comment Tested on Windows 7 64bit with python 2.7.6 and PsychoPy 1.81.03

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('psychopy')
