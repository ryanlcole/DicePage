# 007301.python.hook-gi.repository.GObject.line1.comment -----------------------------------------------------------------------------
# 007302.python.hook-gi.repository.GObject.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007303.python.hook-gi.repository.GObject.line3.comment
# 007304.python.hook-gi.repository.GObject.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007305.python.hook-gi.repository.GObject.line5.comment or later) with exception for distributing the bootloader.
# 007306.python.hook-gi.repository.GObject.line6.comment
# 007307.python.hook-gi.repository.GObject.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007308.python.hook-gi.repository.GObject.line8.comment
# 007309.python.hook-gi.repository.GObject.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007310.python.hook-gi.repository.GObject.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007311.python.hook-gi.repository.GObject.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007312.python.hook-gi.repository.GObject.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
