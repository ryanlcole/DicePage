# 006720.python.hook-scipy.spatial._ckdtree.line1.comment -----------------------------------------------------------------------------
# 006721.python.hook-scipy.spatial._ckdtree.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 006722.python.hook-scipy.spatial._ckdtree.line3.comment
# 006723.python.hook-scipy.spatial._ckdtree.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006724.python.hook-scipy.spatial._ckdtree.line5.comment or later) with exception for distributing the bootloader.
# 006725.python.hook-scipy.spatial._ckdtree.line6.comment
# 006726.python.hook-scipy.spatial._ckdtree.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006727.python.hook-scipy.spatial._ckdtree.line8.comment
# 006728.python.hook-scipy.spatial._ckdtree.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006729.python.hook-scipy.spatial._ckdtree.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 006730.python.hook-scipy.spatial._ckdtree.line14.comment As of SciPy 1.16.0, `scipy.spatial._ckdtree` extension started to depend on newly-introduced `scipy._cyutility`.
if is_module_satisfies('scipy >= 1.16.0'):
    hiddenimports = ['scipy._cyutility']
