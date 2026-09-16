# 007517.python.hook-gi.repository.GstGLX11.line1.comment -----------------------------------------------------------------------------
# 007518.python.hook-gi.repository.GstGLX11.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007519.python.hook-gi.repository.GstGLX11.line3.comment
# 007520.python.hook-gi.repository.GstGLX11.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007521.python.hook-gi.repository.GstGLX11.line5.comment or later) with exception for distributing the bootloader.
# 007522.python.hook-gi.repository.GstGLX11.line6.comment
# 007523.python.hook-gi.repository.GstGLX11.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007524.python.hook-gi.repository.GstGLX11.line8.comment
# 007525.python.hook-gi.repository.GstGLX11.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007526.python.hook-gi.repository.GstGLX11.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007527.python.hook-gi.repository.GstGLX11.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007528.python.hook-gi.repository.GstGLX11.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
