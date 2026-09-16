# 016251.python.hook-pytest.line1.comment ------------------------------------------------------------------
# 016252.python.hook-pytest.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016253.python.hook-pytest.line3.comment
# 016254.python.hook-pytest.line4.comment This file is distributed under the terms of the GNU General Public
# 016255.python.hook-pytest.line5.comment License (version 2.0 or later).
# 016256.python.hook-pytest.line6.comment
# 016257.python.hook-pytest.line7.comment The full license is available in LICENSE, distributed with
# 016258.python.hook-pytest.line8.comment this software.
# 016259.python.hook-pytest.line9.comment
# 016260.python.hook-pytest.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016261.python.hook-pytest.line11.comment ------------------------------------------------------------------
"""
Hook for http://pypi.python.org/pypi/pytest/
"""

import pytest

hiddenimports = pytest.freeze_includes()
