# 020271.python.hook-z3c.rml.line1.comment ------------------------------------------------------------------
# 020272.python.hook-z3c.rml.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 020273.python.hook-z3c.rml.line3.comment
# 020274.python.hook-z3c.rml.line4.comment This file is distributed under the terms of the GNU General Public
# 020275.python.hook-z3c.rml.line5.comment License (version 2.0 or later).
# 020276.python.hook-z3c.rml.line6.comment
# 020277.python.hook-z3c.rml.line7.comment The full license is available in LICENSE, distributed with
# 020278.python.hook-z3c.rml.line8.comment this software.
# 020279.python.hook-z3c.rml.line9.comment
# 020280.python.hook-z3c.rml.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020281.python.hook-z3c.rml.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 020282.python.hook-z3c.rml.line15.comment `z3c.rml` uses Bitstream Vera TTF fonts from the `reportlab` package. As that package can be used without the bundled
# 020283.python.hook-z3c.rml.line16.comment fonts and as some of the bundled fonts have restrictive license (e.g., DarkGarden), we collect the required subset
# 020284.python.hook-z3c.rml.line17.comment of fonts here, instead of collecting them all in a hook for `reportlab`.
datas = collect_data_files(
    "reportlab",
    includes=[
        "fonts/00readme.txt",
        "fonts/bitstream-vera-license.txt",
        "fonts/Vera*.ttf",
    ],
)
