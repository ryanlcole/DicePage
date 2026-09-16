# 007181.python.hook-gi.repository.Adw.line1.comment -----------------------------------------------------------------------------
# 007182.python.hook-gi.repository.Adw.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007183.python.hook-gi.repository.Adw.line3.comment
# 007184.python.hook-gi.repository.Adw.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007185.python.hook-gi.repository.Adw.line5.comment or later) with exception for distributing the bootloader.
# 007186.python.hook-gi.repository.Adw.line6.comment
# 007187.python.hook-gi.repository.Adw.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007188.python.hook-gi.repository.Adw.line8.comment
# 007189.python.hook-gi.repository.Adw.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007190.python.hook-gi.repository.Adw.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007191.python.hook-gi.repository.Adw.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007192.python.hook-gi.repository.Adw.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
