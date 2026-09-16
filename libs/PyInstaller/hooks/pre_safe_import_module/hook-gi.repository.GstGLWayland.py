# 007505.python.hook-gi.repository.GstGLWayland.line1.comment -----------------------------------------------------------------------------
# 007506.python.hook-gi.repository.GstGLWayland.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007507.python.hook-gi.repository.GstGLWayland.line3.comment
# 007508.python.hook-gi.repository.GstGLWayland.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007509.python.hook-gi.repository.GstGLWayland.line5.comment or later) with exception for distributing the bootloader.
# 007510.python.hook-gi.repository.GstGLWayland.line6.comment
# 007511.python.hook-gi.repository.GstGLWayland.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007512.python.hook-gi.repository.GstGLWayland.line8.comment
# 007513.python.hook-gi.repository.GstGLWayland.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007514.python.hook-gi.repository.GstGLWayland.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007515.python.hook-gi.repository.GstGLWayland.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007516.python.hook-gi.repository.GstGLWayland.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
