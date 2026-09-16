# 000153.python.recursion_too_deep_message.line1.comment -----------------------------------------------------------------------------
# 000154.python.recursion_too_deep_message.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 000155.python.recursion_too_deep_message.line3.comment
# 000156.python.recursion_too_deep_message.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 000157.python.recursion_too_deep_message.line5.comment or later) with exception for distributing the bootloader.
# 000158.python.recursion_too_deep_message.line6.comment
# 000159.python.recursion_too_deep_message.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 000160.python.recursion_too_deep_message.line8.comment
# 000161.python.recursion_too_deep_message.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 000162.python.recursion_too_deep_message.line10.comment -----------------------------------------------------------------------------

msg = """
=============================================================
A RecursionError (maximum recursion depth exceeded) occurred.
For working around please follow these instructions
=============================================================

1. In your program's .spec file add this line near the top::

     import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

2. Build your program by running PyInstaller with the .spec file as
   argument::

     pyinstaller myprog.spec

3. If this fails, you most probably hit an endless recursion in
   PyInstaller. Please try to track this down as far as possible,
   create a minimal example so we can reproduce and open an issue at
   https://github.com/pyinstaller/pyinstaller/issues following the
   instructions in the issue template. Many thanks.

Explanation: Python's stack-limit is a safety-belt against endless recursion,
eating up memory. PyInstaller imports modules recursively. If the structure
how modules are imported within your program is awkward, this leads to the
nesting being too deep and hitting Python's stack-limit.

With the default recursion limit (1000), the recursion error occurs at about
115 nested imported, with limit 2000 at about 240, with limit 5000 at about
660.
"""


def raise_with_msg():
    raise SystemExit(msg)
