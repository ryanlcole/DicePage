# 006535.python.hook-pkg_resources.line1.comment -----------------------------------------------------------------------------
# 006536.python.hook-pkg_resources.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006537.python.hook-pkg_resources.line3.comment
# 006538.python.hook-pkg_resources.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006539.python.hook-pkg_resources.line5.comment or later) with exception for distributing the bootloader.
# 006540.python.hook-pkg_resources.line6.comment
# 006541.python.hook-pkg_resources.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006542.python.hook-pkg_resources.line8.comment
# 006543.python.hook-pkg_resources.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006544.python.hook-pkg_resources.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, can_import_module
from PyInstaller.utils.hooks.setuptools import setuptools_info

hiddenimports = []
excludedimports = ['__main__']

# 006545.python.hook-pkg_resources.line18.comment pkg_resources keeps vendored modules in its _vendor subpackage, and does sys.meta_path based import magic to expose
# 006546.python.hook-pkg_resources.line19.comment them as pkg_resources.extern.*
# 006547.python.hook-pkg_resources.line20.comment
# 006548.python.hook-pkg_resources.line21.comment With setuptools >= 71.0, pkg_resources ceased to vendor packages, because vendoring is now done at the setuptools
# 006549.python.hook-pkg_resources.line22.comment level.
if setuptools_info.available and setuptools_info.version < (71, 0, 0):
    # 006550.python.hook-pkg_resources.line24.comment The `railroad` package is an optional requirement for `pyparsing`. `pyparsing.diagrams` depends on `railroad`, so
    # 006551.python.hook-pkg_resources.line25.comment filter it out when `railroad` is not available.
    if can_import_module('railroad'):
        hiddenimports += collect_submodules('pkg_resources._vendor')
    else:
        hiddenimports += collect_submodules(
            'pkg_resources._vendor', filter=lambda name: 'pkg_resources._vendor.pyparsing.diagram' not in name
        )

    # 006552.python.hook-pkg_resources.line33.comment pkg_resources v45.0 dropped support for Python 2 and added this module printing a warning. We could save some
    # 006553.python.hook-pkg_resources.line34.comment bytes if we would replace this by a fake module.
    if setuptools_info.version >= (45, 0, 0) and setuptools_info.version < (49, 1, 1):
        hiddenimports += ['pkg_resources.py2_warn']

    # 006554.python.hook-pkg_resources.line38.comment As of v60.7, setuptools vendored jaraco and has pkg_resources use it. Currently, the pkg_resources._vendor.jaraco
    # 006555.python.hook-pkg_resources.line39.comment namespace package cannot be automatically scanned due to limited support for pure namespace packages in our hook
    # 006556.python.hook-pkg_resources.line40.comment utilities.
    # 006557.python.hook-pkg_resources.line41.comment
    # 006558.python.hook-pkg_resources.line42.comment In setuptools 60.7.0, the vendored jaraco.text package included "Lorem Ipsum.txt" data file, which also has to be
    # 006559.python.hook-pkg_resources.line43.comment collected. However, the presence of the data file (and the resulting directory hierarchy) confuses the importer's
    # 006560.python.hook-pkg_resources.line44.comment redirection logic; instead of trying to work-around that, tell user to upgrade or downgrade their setuptools.
    if setuptools_info.version == (60, 7, 0):
        raise SystemExit(
            "ERROR: Setuptools 60.7.0 is incompatible with PyInstaller. "
            "Downgrade to an earlier version or upgrade to a later version."
        )
    # 006561.python.hook-pkg_resources.line50.comment In setuptools 60.7.1, the "Lorem Ipsum.txt" data file was dropped from the vendored jaraco.text package, so we can
    # 006562.python.hook-pkg_resources.line51.comment accommodate it with couple of hidden imports.
    elif setuptools_info.version >= (60, 7, 1):
        hiddenimports += [
            'pkg_resources._vendor.jaraco.functools',
            'pkg_resources._vendor.jaraco.context',
            'pkg_resources._vendor.jaraco.text',
        ]

    # 006563.python.hook-pkg_resources.line59.comment As of setuptools 70.0.0, we need pkg_resources.extern added to hidden imports.
    if setuptools_info.version >= (70, 0, 0):
        hiddenimports += [
            'pkg_resources.extern',
        ]

# 006564.python.hook-pkg_resources.line65.comment Some more hidden imports. See:
# 006565.python.hook-pkg_resources.line66.comment https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/15#issuecomment-663699288 `packaging` can either be
# 006566.python.hook-pkg_resources.line67.comment its own package, or embedded in `pkg_resources._vendor.packaging`, or both.
hiddenimports += collect_submodules('packaging')
