# 011516.python.pyi_rth_ffpyplayer.line1.comment -----------------------------------------------------------------------------
# 011517.python.pyi_rth_ffpyplayer.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 011518.python.pyi_rth_ffpyplayer.line3.comment
# 011519.python.pyi_rth_ffpyplayer.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011520.python.pyi_rth_ffpyplayer.line5.comment
# 011521.python.pyi_rth_ffpyplayer.line6.comment The full license is available in LICENSE, distributed with
# 011522.python.pyi_rth_ffpyplayer.line7.comment this software.
# 011523.python.pyi_rth_ffpyplayer.line8.comment
# 011524.python.pyi_rth_ffpyplayer.line9.comment SPDX-License-Identifier: Apache-2.0
# 011525.python.pyi_rth_ffpyplayer.line10.comment -----------------------------------------------------------------------------

# 011526.python.pyi_rth_ffpyplayer.line12.comment Starting with v4.3.5, the `ffpyplayer` package attempts to use `site.USER_BASE` in path manipulation functions.
# 011527.python.pyi_rth_ffpyplayer.line13.comment As frozen application runs with disabled `site`, the value of this variable is `None`, and causes path manipulation
# 011528.python.pyi_rth_ffpyplayer.line14.comment functions to raise an error. As a work-around, we set `site.USER_BASE` to an empty string, which is also what the
# 011529.python.pyi_rth_ffpyplayer.line15.comment fake `site` module available in PyInstaller prior to v5.5 did.
import site

if site.USER_BASE is None:
    site.USER_BASE = ''
