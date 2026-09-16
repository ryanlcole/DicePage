# 005252.python.hook-_osx_support.line1.comment -----------------------------------------------------------------------------
# 005253.python.hook-_osx_support.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 005254.python.hook-_osx_support.line3.comment
# 005255.python.hook-_osx_support.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005256.python.hook-_osx_support.line5.comment or later) with exception for distributing the bootloader.
# 005257.python.hook-_osx_support.line6.comment
# 005258.python.hook-_osx_support.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005259.python.hook-_osx_support.line8.comment
# 005260.python.hook-_osx_support.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005261.python.hook-_osx_support.line10.comment -----------------------------------------------------------------------------

# 005262.python.hook-_osx_support.line12.comment Prevent conditional import of `distutils` in `_osx_support.compiler_fixup()` in python < 3.10 from pulling in
# 005263.python.hook-_osx_support.line13.comment `distutils`; this function is called only from `distutils` itself, which ensures that the module is available as
# 005264.python.hook-_osx_support.line14.comment needed. Blocking this import prevents `distutils` (and nowadays `setuptools`) from being pulled into even very
# 005265.python.hook-_osx_support.line15.comment basic applications when built with python < 3.10.
# 005266.python.hook-_osx_support.line16.comment
# 005267.python.hook-_osx_support.line17.comment See: https://github.com/python/cpython/blob/f3994ade31a563d49806cf6a681d1b1115fccaa3/Lib/_osx_support.py#L430-L434

excludedimports = ['distutils']
