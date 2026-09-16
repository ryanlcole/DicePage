# 017630.python.hook-toga_winforms.line1.comment ------------------------------------------------------------------
# 017631.python.hook-toga_winforms.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017632.python.hook-toga_winforms.line3.comment
# 017633.python.hook-toga_winforms.line4.comment This file is distributed under the terms of the GNU General Public
# 017634.python.hook-toga_winforms.line5.comment License (version 2.0 or later).
# 017635.python.hook-toga_winforms.line6.comment
# 017636.python.hook-toga_winforms.line7.comment The full license is available in LICENSE, distributed with
# 017637.python.hook-toga_winforms.line8.comment this software.
# 017638.python.hook-toga_winforms.line9.comment
# 017639.python.hook-toga_winforms.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017640.python.hook-toga_winforms.line11.comment ------------------------------------------------------------------

import os

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# 017641.python.hook-toga_winforms.line17.comment Collect default icon from `resources`, and license/readme file from  `toga_winforms/libs/WebView2`. Use the same call
# 017642.python.hook-toga_winforms.line18.comment to also collect bundled WebView2 DLLs from `toga_winforms/libs/WebView2`.
include_patterns = [
    'resources/*',
    'libs/WebView2/*.md',
    'libs/WebView2/*.dll',
]

# 017643.python.hook-toga_winforms.line25.comment The package seems to bundle WebView2 runtimes for x86, x64, and arm64. We need to collect only the one for the
# 017644.python.hook-toga_winforms.line26.comment running platform, which can be reliably identified by `PROCESSOR_ARCHITECTURE` environment variable, which properly
# 017645.python.hook-toga_winforms.line27.comment reflects the processor architecture of running process (even if running x86 python on x64 machine, or x64 python on
# 017646.python.hook-toga_winforms.line28.comment arm64 machine).
machine = os.environ["PROCESSOR_ARCHITECTURE"].lower()
if machine == 'x86':
    include_patterns += ['libs/WebView2/runtimes/win-x86/*']
elif machine == 'amd64':
    include_patterns += ['libs/WebView2/runtimes/win-x64/*']
elif machine == 'arm64':
    include_patterns += ['libs/WebView2/runtimes/win-arm64/*']

datas = collect_data_files('toga_winforms', includes=include_patterns)

# 017647.python.hook-toga_winforms.line39.comment Collect metadata so that the backend can be discovered via `toga.backends` entry-point.
datas += copy_metadata("toga-winforms")
