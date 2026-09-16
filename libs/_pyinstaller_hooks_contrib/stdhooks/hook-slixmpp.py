# 017151.python.hook-slixmpp.line1.comment ------------------------------------------------------------------
# 017152.python.hook-slixmpp.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017153.python.hook-slixmpp.line3.comment
# 017154.python.hook-slixmpp.line4.comment This file is distributed under the terms of the GNU General Public
# 017155.python.hook-slixmpp.line5.comment License (version 2.0 or later).
# 017156.python.hook-slixmpp.line6.comment
# 017157.python.hook-slixmpp.line7.comment The full license is available in LICENSE, distributed with
# 017158.python.hook-slixmpp.line8.comment this software.
# 017159.python.hook-slixmpp.line9.comment
# 017160.python.hook-slixmpp.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017161.python.hook-slixmpp.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("slixmpp.features")
