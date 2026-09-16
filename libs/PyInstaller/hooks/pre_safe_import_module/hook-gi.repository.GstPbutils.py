# 007565.python.hook-gi.repository.GstPbutils.line1.comment -----------------------------------------------------------------------------
# 007566.python.hook-gi.repository.GstPbutils.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007567.python.hook-gi.repository.GstPbutils.line3.comment
# 007568.python.hook-gi.repository.GstPbutils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007569.python.hook-gi.repository.GstPbutils.line5.comment or later) with exception for distributing the bootloader.
# 007570.python.hook-gi.repository.GstPbutils.line6.comment
# 007571.python.hook-gi.repository.GstPbutils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007572.python.hook-gi.repository.GstPbutils.line8.comment
# 007573.python.hook-gi.repository.GstPbutils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007574.python.hook-gi.repository.GstPbutils.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007575.python.hook-gi.repository.GstPbutils.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007576.python.hook-gi.repository.GstPbutils.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
