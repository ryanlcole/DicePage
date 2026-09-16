# 006743.python.hook-scipy.special._ellip_harm_2.line1.comment -----------------------------------------------------------------------------
# 006744.python.hook-scipy.special._ellip_harm_2.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006745.python.hook-scipy.special._ellip_harm_2.line3.comment
# 006746.python.hook-scipy.special._ellip_harm_2.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006747.python.hook-scipy.special._ellip_harm_2.line5.comment or later) with exception for distributing the bootloader.
# 006748.python.hook-scipy.special._ellip_harm_2.line6.comment
# 006749.python.hook-scipy.special._ellip_harm_2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006750.python.hook-scipy.special._ellip_harm_2.line8.comment
# 006751.python.hook-scipy.special._ellip_harm_2.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006752.python.hook-scipy.special._ellip_harm_2.line10.comment -----------------------------------------------------------------------------
"""
Module hook for the `scipy.special._ellip_harm_2` C extension first introduced by SciPy >= 0.15.0.

See Also
----------
https://github.com/scipy/scipy/blob/master/scipy/special/_ellip_harm_2.pyx
    This C extension's Cython-based implementation.
"""

# 006753.python.hook-scipy.special._ellip_harm_2.line20.comment In SciPy >= 0.15.0:
# 006754.python.hook-scipy.special._ellip_harm_2.line21.comment
# 006755.python.hook-scipy.special._ellip_harm_2.line22.comment 1. The "scipy.special.__init__" module imports...
# 006756.python.hook-scipy.special._ellip_harm_2.line23.comment 2. The "scipy.special._ellip_harm" module imports...
# 006757.python.hook-scipy.special._ellip_harm_2.line24.comment 3. The "scipy.special._ellip_harm_2" C extension imports...
# 006758.python.hook-scipy.special._ellip_harm_2.line25.comment 4. The "scipy.integrate" package.
# 006759.python.hook-scipy.special._ellip_harm_2.line26.comment
# 006760.python.hook-scipy.special._ellip_harm_2.line27.comment The third import is undetectable by PyInstaller and hence explicitly listed. Since "_ellip_harm" and "_ellip_harm_2"
# 006761.python.hook-scipy.special._ellip_harm_2.line28.comment were first introduced by SciPy 0.15.0, the following hidden import will only be applied for versions of SciPy
# 006762.python.hook-scipy.special._ellip_harm_2.line29.comment guaranteed to provide these modules and C extensions.
hiddenimports = ['scipy.integrate']
