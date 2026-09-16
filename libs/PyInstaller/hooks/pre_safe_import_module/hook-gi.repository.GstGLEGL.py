# 007493.python.hook-gi.repository.GstGLEGL.line1.comment -----------------------------------------------------------------------------
# 007494.python.hook-gi.repository.GstGLEGL.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007495.python.hook-gi.repository.GstGLEGL.line3.comment
# 007496.python.hook-gi.repository.GstGLEGL.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007497.python.hook-gi.repository.GstGLEGL.line5.comment or later) with exception for distributing the bootloader.
# 007498.python.hook-gi.repository.GstGLEGL.line6.comment
# 007499.python.hook-gi.repository.GstGLEGL.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007500.python.hook-gi.repository.GstGLEGL.line8.comment
# 007501.python.hook-gi.repository.GstGLEGL.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007502.python.hook-gi.repository.GstGLEGL.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007503.python.hook-gi.repository.GstGLEGL.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007504.python.hook-gi.repository.GstGLEGL.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
