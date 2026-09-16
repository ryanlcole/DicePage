# 006215.python.hook-keyring.line1.comment -----------------------------------------------------------------------------
# 006216.python.hook-keyring.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 006217.python.hook-keyring.line3.comment
# 006218.python.hook-keyring.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006219.python.hook-keyring.line5.comment or later) with exception for distributing the bootloader.
# 006220.python.hook-keyring.line6.comment
# 006221.python.hook-keyring.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006222.python.hook-keyring.line8.comment
# 006223.python.hook-keyring.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006224.python.hook-keyring.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

# 006225.python.hook-keyring.line14.comment Collect backends
hiddenimports = collect_submodules('keyring.backends')

# 006226.python.hook-keyring.line17.comment Keyring performs backend plugin discovery using setuptools entry points, which are listed in the metadata. Therefore,
# 006227.python.hook-keyring.line18.comment we need to copy the metadata, otherwise no backends will be found at run-time.
datas = copy_metadata('keyring')
