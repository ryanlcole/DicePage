# 007265.python.hook-gi.repository.GIRepository.line1.comment -----------------------------------------------------------------------------
# 007266.python.hook-gi.repository.GIRepository.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007267.python.hook-gi.repository.GIRepository.line3.comment
# 007268.python.hook-gi.repository.GIRepository.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007269.python.hook-gi.repository.GIRepository.line5.comment or later) with exception for distributing the bootloader.
# 007270.python.hook-gi.repository.GIRepository.line6.comment
# 007271.python.hook-gi.repository.GIRepository.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007272.python.hook-gi.repository.GIRepository.line8.comment
# 007273.python.hook-gi.repository.GIRepository.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007274.python.hook-gi.repository.GIRepository.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007275.python.hook-gi.repository.GIRepository.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007276.python.hook-gi.repository.GIRepository.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
