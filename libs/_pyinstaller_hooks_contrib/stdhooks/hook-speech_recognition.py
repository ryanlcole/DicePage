# 017216.python.hook-speech_recognition.line1.comment ------------------------------------------------------------------
# 017217.python.hook-speech_recognition.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017218.python.hook-speech_recognition.line3.comment
# 017219.python.hook-speech_recognition.line4.comment This file is distributed under the terms of the GNU General Public
# 017220.python.hook-speech_recognition.line5.comment License (version 2.0 or later).
# 017221.python.hook-speech_recognition.line6.comment
# 017222.python.hook-speech_recognition.line7.comment The full license is available in LICENSE, distributed with
# 017223.python.hook-speech_recognition.line8.comment this software.
# 017224.python.hook-speech_recognition.line9.comment
# 017225.python.hook-speech_recognition.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017226.python.hook-speech_recognition.line11.comment ------------------------------------------------------------------

# 017227.python.hook-speech_recognition.line13.comment Hook for speech_recognition: https://pypi.python.org/pypi/SpeechRecognition/
# 017228.python.hook-speech_recognition.line14.comment Tested on Windows 8.1 x64 with SpeechRecognition 1.5

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("speech_recognition")
