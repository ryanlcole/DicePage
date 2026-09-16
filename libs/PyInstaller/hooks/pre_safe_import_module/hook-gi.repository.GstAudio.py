# 007409.python.hook-gi.repository.GstAudio.line1.comment -----------------------------------------------------------------------------
# 007410.python.hook-gi.repository.GstAudio.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007411.python.hook-gi.repository.GstAudio.line3.comment
# 007412.python.hook-gi.repository.GstAudio.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007413.python.hook-gi.repository.GstAudio.line5.comment or later) with exception for distributing the bootloader.
# 007414.python.hook-gi.repository.GstAudio.line6.comment
# 007415.python.hook-gi.repository.GstAudio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007416.python.hook-gi.repository.GstAudio.line8.comment
# 007417.python.hook-gi.repository.GstAudio.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007418.python.hook-gi.repository.GstAudio.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007419.python.hook-gi.repository.GstAudio.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007420.python.hook-gi.repository.GstAudio.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
