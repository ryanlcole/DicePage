# 006395.python.hook-multiprocessing.util.line1.comment -----------------------------------------------------------------------------
# 006396.python.hook-multiprocessing.util.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006397.python.hook-multiprocessing.util.line3.comment
# 006398.python.hook-multiprocessing.util.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006399.python.hook-multiprocessing.util.line5.comment or later) with exception for distributing the bootloader.
# 006400.python.hook-multiprocessing.util.line6.comment
# 006401.python.hook-multiprocessing.util.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006402.python.hook-multiprocessing.util.line8.comment
# 006403.python.hook-multiprocessing.util.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006404.python.hook-multiprocessing.util.line10.comment -----------------------------------------------------------------------------

# 006405.python.hook-multiprocessing.util.line12.comment In Python 3.8 mutliprocess.utils has _cleanup_tests() to cleanup multiprocessing resources when multiprocessing tests
# 006406.python.hook-multiprocessing.util.line13.comment completed. This function import `tests` which is the complete Python test-suite, pulling in many more dependencies,
# 006407.python.hook-multiprocessing.util.line14.comment e.g., tkinter.

excludedimports = ['test']
