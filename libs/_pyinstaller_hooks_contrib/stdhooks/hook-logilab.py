# 014396.python.hook-logilab.line1.comment ------------------------------------------------------------------
# 014397.python.hook-logilab.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014398.python.hook-logilab.line3.comment
# 014399.python.hook-logilab.line4.comment This file is distributed under the terms of the GNU General Public
# 014400.python.hook-logilab.line5.comment License (version 2.0 or later).
# 014401.python.hook-logilab.line6.comment
# 014402.python.hook-logilab.line7.comment The full license is available in LICENSE, distributed with
# 014403.python.hook-logilab.line8.comment this software.
# 014404.python.hook-logilab.line9.comment
# 014405.python.hook-logilab.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014406.python.hook-logilab.line11.comment ------------------------------------------------------------------
# 014407.python.hook-logilab.line12.comment
# 014408.python.hook-logilab.line13.comment ***************************************************
# 014409.python.hook-logilab.line14.comment hook-logilab.py - PyInstaller hook file for logilab
# 014410.python.hook-logilab.line15.comment ***************************************************
# 014411.python.hook-logilab.line16.comment The following was written about logilab, version 1.1.0, based on executing
# 014412.python.hook-logilab.line17.comment ``pip show logilab-common``.
# 014413.python.hook-logilab.line18.comment
# 014414.python.hook-logilab.line19.comment In logilab.common, line 33::
# 014415.python.hook-logilab.line20.comment
# 014416.python.hook-logilab.line21.comment __version__ = pkg_resources.get_distribution('logilab-common').version
# 014417.python.hook-logilab.line22.comment
# 014418.python.hook-logilab.line23.comment Therefore, we need metadata for logilab.
from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('logilab-common')
