# 007373.python.hook-gi.repository.Gst.line1.comment -----------------------------------------------------------------------------
# 007374.python.hook-gi.repository.Gst.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007375.python.hook-gi.repository.Gst.line3.comment
# 007376.python.hook-gi.repository.Gst.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007377.python.hook-gi.repository.Gst.line5.comment or later) with exception for distributing the bootloader.
# 007378.python.hook-gi.repository.Gst.line6.comment
# 007379.python.hook-gi.repository.Gst.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007380.python.hook-gi.repository.Gst.line8.comment
# 007381.python.hook-gi.repository.Gst.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007382.python.hook-gi.repository.Gst.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007383.python.hook-gi.repository.Gst.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007384.python.hook-gi.repository.Gst.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
