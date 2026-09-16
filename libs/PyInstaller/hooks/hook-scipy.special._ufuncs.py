# 006763.python.hook-scipy.special._ufuncs.line1.comment -----------------------------------------------------------------------------
# 006764.python.hook-scipy.special._ufuncs.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006765.python.hook-scipy.special._ufuncs.line3.comment
# 006766.python.hook-scipy.special._ufuncs.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006767.python.hook-scipy.special._ufuncs.line5.comment or later) with exception for distributing the bootloader.
# 006768.python.hook-scipy.special._ufuncs.line6.comment
# 006769.python.hook-scipy.special._ufuncs.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006770.python.hook-scipy.special._ufuncs.line8.comment
# 006771.python.hook-scipy.special._ufuncs.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006772.python.hook-scipy.special._ufuncs.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 006773.python.hook-scipy.special._ufuncs.line14.comment Module scipy.io._ufunc depends on some other C/C++ extensions. The hidden import is necessary for SciPy 0.13+.
# 006774.python.hook-scipy.special._ufuncs.line15.comment Thanks to dyadkin; see issue #826.
hiddenimports = ['scipy.special._ufuncs_cxx']

# 006775.python.hook-scipy.special._ufuncs.line18.comment SciPy 1.13.0 cythonized cdflib; this introduced new `scipy.special._cdflib` extension that is imported from the
# 006776.python.hook-scipy.special._ufuncs.line19.comment `scipy.special._ufuncs` extension, and thus we need a hidden import here.
if is_module_satisfies('scipy >= 1.13.0'):
    hiddenimports += ['scipy.special._cdflib']

# 006777.python.hook-scipy.special._ufuncs.line23.comment SciPy 1.14.0 introduced `scipy.special._special_ufuncs`, which is imported from `scipy.special._ufuncs` extension.
if is_module_satisfies('scipy >= 1.14.0'):
    hiddenimports += ['scipy.special._special_ufuncs']
