# 007349.python.hook-gi.repository.Graphene.line1.comment -----------------------------------------------------------------------------
# 007350.python.hook-gi.repository.Graphene.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007351.python.hook-gi.repository.Graphene.line3.comment
# 007352.python.hook-gi.repository.Graphene.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007353.python.hook-gi.repository.Graphene.line5.comment or later) with exception for distributing the bootloader.
# 007354.python.hook-gi.repository.Graphene.line6.comment
# 007355.python.hook-gi.repository.Graphene.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007356.python.hook-gi.repository.Graphene.line8.comment
# 007357.python.hook-gi.repository.Graphene.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007358.python.hook-gi.repository.Graphene.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007359.python.hook-gi.repository.Graphene.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007360.python.hook-gi.repository.Graphene.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
