# 011836.python.hook-OpenGL_accelerate.line1.comment ------------------------------------------------------------------
# 011837.python.hook-OpenGL_accelerate.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011838.python.hook-OpenGL_accelerate.line3.comment
# 011839.python.hook-OpenGL_accelerate.line4.comment This file is distributed under the terms of the GNU General Public
# 011840.python.hook-OpenGL_accelerate.line5.comment License (version 2.0 or later).
# 011841.python.hook-OpenGL_accelerate.line6.comment
# 011842.python.hook-OpenGL_accelerate.line7.comment The full license is available in LICENSE, distributed with
# 011843.python.hook-OpenGL_accelerate.line8.comment this software.
# 011844.python.hook-OpenGL_accelerate.line9.comment
# 011845.python.hook-OpenGL_accelerate.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011846.python.hook-OpenGL_accelerate.line11.comment ------------------------------------------------------------------
"""
OpenGL_accelerate contais modules written in cython. This module
should speed up some functions from OpenGL module. The following
hiddenimports are not resolved by PyInstaller because OpenGL_accelerate
is compiled to native Python modules.
"""

hiddenimports = [
    'OpenGL_accelerate.wrapper',
    'OpenGL_accelerate.formathandler',
]
