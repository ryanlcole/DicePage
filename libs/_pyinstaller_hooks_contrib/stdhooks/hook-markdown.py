# 014522.python.hook-markdown.line1.comment ------------------------------------------------------------------
# 014523.python.hook-markdown.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014524.python.hook-markdown.line3.comment
# 014525.python.hook-markdown.line4.comment This file is distributed under the terms of the GNU General Public
# 014526.python.hook-markdown.line5.comment License (version 2.0 or later).
# 014527.python.hook-markdown.line6.comment
# 014528.python.hook-markdown.line7.comment The full license is available in LICENSE, distributed with
# 014529.python.hook-markdown.line8.comment this software.
# 014530.python.hook-markdown.line9.comment
# 014531.python.hook-markdown.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014532.python.hook-markdown.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import (
    collect_submodules,
    copy_metadata,
    is_module_satisfies,
)

hiddenimports = collect_submodules('markdown.extensions')

# 014533.python.hook-markdown.line21.comment Markdown 3.3 introduced markdown.htmlparser submodule with hidden
# 014534.python.hook-markdown.line22.comment dependency on html.parser
if is_module_satisfies("markdown >= 3.3"):
    hiddenimports += ['html.parser']

# 014535.python.hook-markdown.line26.comment Extensions can be referenced by short names, e.g. "extra", through a mechanism
# 014536.python.hook-markdown.line27.comment using entry-points. Thus we need to collect the package metadata as well.
datas = copy_metadata("markdown")
