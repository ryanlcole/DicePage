# 011386.python.init.line1.comment ------------------------------------------------------------------
# 011387.python.init.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011388.python.init.line3.comment
# 011389.python.init.line4.comment This file is distributed under the terms of the GNU General Public
# 011390.python.init.line5.comment License (version 2.0 or later).
# 011391.python.init.line6.comment
# 011392.python.init.line7.comment The full license is available in LICENSE, distributed with
# 011393.python.init.line8.comment this software.
# 011394.python.init.line9.comment
# 011395.python.init.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011396.python.init.line11.comment ------------------------------------------------------------------

import sys

__version__ = '2025.9'
__maintainer__ = 'Legorooj, bwoodsend'
__uri__ = 'https://github.com/pyinstaller/pyinstaller-hooks-contrib'


def get_hook_dirs():
    import os
    hooks_dir = os.path.dirname(__file__)
    return [
        # 011397.python.init.line24.comment Required because standard hooks are in sub-directory instead of the top-level hooks directory.
        os.path.join(hooks_dir, 'stdhooks'),
        # 011398.python.init.line26.comment pre_* and run-time hooks
        hooks_dir,
    ]


# 011399.python.init.line31.comment Several packages for which provide hooks are involved in deep dependency chains when various optional dependencies are
# 011400.python.init.line32.comment installed in the environment, and their analysis typically requires recursion limit that exceeds the default 1000.
# 011401.python.init.line33.comment Therefore, automatically raise the recursion limit to at least 5000. This alleviates the need to do so on per-hook
# 011402.python.init.line34.comment basis.
if (sys.platform.startswith('win') or sys.platform == 'cygwin') and sys.version_info < (3, 11):
    # 011403.python.init.line36.comment The recursion limit test in PyInstaller main repository seems to push the recursion level to the limit; and if the
    # 011404.python.init.line37.comment limit is set to 5000, this crashes python 3.8 - 3.10 on Windows and 3.9 that is (at the time of writing) available
    # 011405.python.init.line38.comment under Cygwin. Further investigation revealed that Windows builds of python 3.8 and 3.10 handle recursion up to
    # 011406.python.init.line39.comment level ~2075, while the practical limit for 3.9 is between 1950 and 1975. Therefore, for affected combinations of
    # 011407.python.init.line40.comment platforms and python versions, use a conservative limit of 1900 - if only to avoid issues with the recursion limit
    # 011408.python.init.line41.comment test in the main PyInstaller repository...
    new_recursion_limit = 1900
else:
    new_recursion_limit = 5000

if sys.getrecursionlimit() < new_recursion_limit:
    sys.setrecursionlimit(new_recursion_limit)
