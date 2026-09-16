# 013002.python.hook-dns.rdata.line1.comment ------------------------------------------------------------------
# 013003.python.hook-dns.rdata.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013004.python.hook-dns.rdata.line3.comment
# 013005.python.hook-dns.rdata.line4.comment This file is distributed under the terms of the GNU General Public
# 013006.python.hook-dns.rdata.line5.comment License (version 2.0 or later).
# 013007.python.hook-dns.rdata.line6.comment
# 013008.python.hook-dns.rdata.line7.comment The full license is available in LICENSE, distributed with
# 013009.python.hook-dns.rdata.line8.comment this software.
# 013010.python.hook-dns.rdata.line9.comment
# 013011.python.hook-dns.rdata.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013012.python.hook-dns.rdata.line11.comment ------------------------------------------------------------------

# 013013.python.hook-dns.rdata.line13.comment This is hook for DNS python package dnspython.

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('dns.rdtypes')
