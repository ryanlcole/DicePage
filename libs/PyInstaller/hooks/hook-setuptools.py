# 006826.python.hook-setuptools.line1.comment -----------------------------------------------------------------------------
# 006827.python.hook-setuptools.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006828.python.hook-setuptools.line3.comment
# 006829.python.hook-setuptools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006830.python.hook-setuptools.line5.comment or later) with exception for distributing the bootloader.
# 006831.python.hook-setuptools.line6.comment
# 006832.python.hook-setuptools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006833.python.hook-setuptools.line8.comment
# 006834.python.hook-setuptools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006835.python.hook-setuptools.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat
from PyInstaller.utils.hooks.setuptools import setuptools_info

datas = []

hiddenimports = [
    # 006836.python.hook-setuptools.line18.comment Test case import/test_zipimport2 fails during importing pkg_resources or setuptools when module not present.
    'distutils.command.build_ext',
    'setuptools.msvc',
]

# 006837.python.hook-setuptools.line23.comment Necessary for setuptools on Mac/Unix
if compat.is_unix or compat.is_darwin:
    hiddenimports.append('syslog')

# 006838.python.hook-setuptools.line27.comment Prevent the following modules from being collected solely due to reference from anywhere within setuptools (or
# 006839.python.hook-setuptools.line28.comment its vendored dependencies).
excludedimports = [
    'pytest',
    'numpy',  # originally from hook-setuptools.msvc
    'docutils',  # originally from hool-setuptools._distutils.command.check
]

# 006842.python.hook-setuptools.line35.comment setuptools >= 39.0.0 is "vendoring" its own direct dependencies from "_vendor" to "extern". This also requires
# 006843.python.hook-setuptools.line36.comment 'pre_safe_import_module/hook-setuptools.extern.six.moves.py' to make the moves defined in 'setuptools._vendor.six'
# 006844.python.hook-setuptools.line37.comment importable under 'setuptools.extern.six'.
# 006845.python.hook-setuptools.line38.comment
# 006846.python.hook-setuptools.line39.comment With setuptools 71.0.0, the vendored packages are exposed to the outside world by `setuptools._vendor` location being
# 006847.python.hook-setuptools.line40.comment appended to `sys.path`, and the `VendorImporter` is gone (i.e., no more mapping to `setuptools.extern`). Since the
# 006848.python.hook-setuptools.line41.comment vendored dependencies are now exposed as top-level modules (provided upstream versions are not available, as they
# 006849.python.hook-setuptools.line42.comment would take precedence due to `sys.path` ordering), we need pre-safe-import-module hooks that detect when only vendored
# 006850.python.hook-setuptools.line43.comment version is available, and add aliases to prevent duplicated collection. For list of vendored packages for which we
# 006851.python.hook-setuptools.line44.comment need such pre-safe-import-module hooks, see the code in `PyInstaller.utils.hooks.setuptools`.
# 006852.python.hook-setuptools.line45.comment
# 006853.python.hook-setuptools.line46.comment The list of submodules from `setuptools._vendor` is now available in `setuptools_info.vendored_modules` (and covers
# 006854.python.hook-setuptools.line47.comment all setuptools versions).
# 006855.python.hook-setuptools.line48.comment
# 006856.python.hook-setuptools.line49.comment NOTE: with setuptools >= 71.0, we do not need to add modules from `setuptools._vendored` to hidden imports anymore,
# 006857.python.hook-setuptools.line50.comment because the aliases we set up should ensure that the necessary parts get collected. We still need them for earlier
# 006858.python.hook-setuptools.line51.comment versions of setuptools, though.
if setuptools_info.version < (71, 0):
    hiddenimports += setuptools_info.vendored_modules

# 006859.python.hook-setuptools.line55.comment The situation with vendored distutils (from `setuptools._distutils`) is a bit more complicated; python >= 3.12 does
# 006860.python.hook-setuptools.line56.comment not provide stdlib version of `distutils` anymore, so our corresponding pre-safe-import-module hook sets up aliases.
# 006861.python.hook-setuptools.line57.comment In earlier python versions, stdlib version is available as well, and at run-time, we might need both versions present,
# 006862.python.hook-setuptools.line58.comment so that whichever is applicable can be used. Therefore, for python < 3.12, we need to add the vendored distuils
# 006863.python.hook-setuptools.line59.comment modules to hidden imports.
if setuptools_info.distutils_vendored and not compat.is_py312:
    hiddenimports += setuptools_info.distutils_modules

# 006864.python.hook-setuptools.line63.comment With setuptools >= 71.0.0, the vendored packages also have metadata, and might also contain data files that need to
# 006865.python.hook-setuptools.line64.comment be collected. The list of corresponding data files is kept cached in `setuptools_info.vendored_data` (to minimize the
# 006866.python.hook-setuptools.line65.comment number of times we need to call collect_data_files()).
# 006867.python.hook-setuptools.line66.comment
# 006868.python.hook-setuptools.line67.comment While it might be tempting to simply collect all data files and be done with it, we actually need to match the
# 006869.python.hook-setuptools.line68.comment collection behavior for the stand-alone versions of these packages; i.e., we should collect metadata (and/or data
# 006870.python.hook-setuptools.line69.comment files) for the vendored package only if the same data is also collected for stand-alone version. Otherwise, we risk
# 006871.python.hook-setuptools.line70.comment inconsistent behavior and potential mismatches; for example, if we collected metadata for vendored package A here,
# 006872.python.hook-setuptools.line71.comment but end up collecting stand-alone A, for which we normally do not collect the metadata, then at run-time, we will end
# 006873.python.hook-setuptools.line72.comment up with stand-alone copy of A and vendored copy of its metadata being discoverable.
# 006874.python.hook-setuptools.line73.comment
# 006875.python.hook-setuptools.line74.comment Therefore, if metadata and/or metadata needs to be collected, do it in corresponding sub-package hook (for an example,
# 006876.python.hook-setuptools.line75.comment see `hook-setuptools._vendor.jaraco.text.py`).
