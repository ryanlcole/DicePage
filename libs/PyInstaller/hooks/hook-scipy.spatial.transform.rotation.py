# 006731.python.hook-scipy.spatial.transform.rotation.line1.comment -----------------------------------------------------------------------------
# 006732.python.hook-scipy.spatial.transform.rotation.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 006733.python.hook-scipy.spatial.transform.rotation.line3.comment
# 006734.python.hook-scipy.spatial.transform.rotation.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006735.python.hook-scipy.spatial.transform.rotation.line5.comment or later) with exception for distributing the bootloader.
# 006736.python.hook-scipy.spatial.transform.rotation.line6.comment
# 006737.python.hook-scipy.spatial.transform.rotation.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006738.python.hook-scipy.spatial.transform.rotation.line8.comment
# 006739.python.hook-scipy.spatial.transform.rotation.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006740.python.hook-scipy.spatial.transform.rotation.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import check_requirement

# 006741.python.hook-scipy.spatial.transform.rotation.line14.comment As of scipy 1.6.0, scipy.spatial.transform.rotation is cython-compiled, so we fail to automatically pick up its
# 006742.python.hook-scipy.spatial.transform.rotation.line15.comment imports.
if check_requirement("scipy >= 1.6.0"):
    hiddenimports = ['scipy.spatial.transform._rotation_groups']
