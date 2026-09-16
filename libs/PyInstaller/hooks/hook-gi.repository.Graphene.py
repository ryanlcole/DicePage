# 005695.python.hook-gi.repository.Graphene.line1.comment -----------------------------------------------------------------------------
# 005696.python.hook-gi.repository.Graphene.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005697.python.hook-gi.repository.Graphene.line3.comment
# 005698.python.hook-gi.repository.Graphene.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005699.python.hook-gi.repository.Graphene.line5.comment or later) with exception for distributing the bootloader.
# 005700.python.hook-gi.repository.Graphene.line6.comment
# 005701.python.hook-gi.repository.Graphene.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005702.python.hook-gi.repository.Graphene.line8.comment
# 005703.python.hook-gi.repository.Graphene.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005704.python.hook-gi.repository.Graphene.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Graphene', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
