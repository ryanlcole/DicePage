# 005350.python.hook-distutils.util.line1.comment -----------------------------------------------------------------------------
# 005351.python.hook-distutils.util.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005352.python.hook-distutils.util.line3.comment
# 005353.python.hook-distutils.util.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005354.python.hook-distutils.util.line5.comment or later) with exception for distributing the bootloader.
# 005355.python.hook-distutils.util.line6.comment
# 005356.python.hook-distutils.util.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005357.python.hook-distutils.util.line8.comment
# 005358.python.hook-distutils.util.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005359.python.hook-distutils.util.line10.comment -----------------------------------------------------------------------------

# 005360.python.hook-distutils.util.line12.comment distutils.util.run_2to3() imports lib2to3. Exclude it as chances are low that it is used by the frozen package.
excludedimports = ['lib2to3.refactor']
