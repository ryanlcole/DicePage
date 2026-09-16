# 007155.python.hook-gi.line1.comment -----------------------------------------------------------------------------
# 007156.python.hook-gi.line2.comment Copyright (c) 2022-2023, PyInstaller Development Team.
# 007157.python.hook-gi.line3.comment
# 007158.python.hook-gi.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007159.python.hook-gi.line5.comment or later) with exception for distributing the bootloader.
# 007160.python.hook-gi.line6.comment
# 007161.python.hook-gi.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007162.python.hook-gi.line8.comment
# 007163.python.hook-gi.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007164.python.hook-gi.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat
from PyInstaller.utils import hooks as hookutils


def pre_safe_import_module(api):
    if compat.is_linux:
        # 007165.python.hook-gi.line18.comment RHEL/Fedora RPM package for GObject introspection is known to split the `gi` package into two locations:
        # 007166.python.hook-gi.line19.comment - /usr/lib64/python3.x/site-packages/gi
        # 007167.python.hook-gi.line20.comment - /usr/lib/python3.x/site-packages/gi
        # 007168.python.hook-gi.line21.comment The `__init__.py` is located in the first directory, while `repository` and `overrides` are located in
        # 007169.python.hook-gi.line22.comment the second, and `__init__.py` dynamically extends the `__path__` during package import, using
        # 007170.python.hook-gi.line23.comment `__path__ = pkgutil.extend_path(__path__, __name__)`.
        # 007171.python.hook-gi.line24.comment The modulegraph has no way of knowing this, so we need extend the package path in this hook. Otherwise,
        # 007172.python.hook-gi.line25.comment only the first location is scanned, and the `gi.repository` ends up missing.
        # 007173.python.hook-gi.line26.comment
        # 007174.python.hook-gi.line27.comment ADDENDUM: it looks like the `gi.overrides` can also be split across both locations, so we need a similar
        # 007175.python.hook-gi.line28.comment hook for `gi.overrides` as well.
        # 007176.python.hook-gi.line29.comment
        # 007177.python.hook-gi.line30.comment NOTE: the `get_package_paths`/`get_package_all_paths` helpers read the paths from package's spec without
        # 007178.python.hook-gi.line31.comment importing the (top-level) package, so they do not catch run-time path modifications. Instead, we use
        # 007179.python.hook-gi.line32.comment `get_module_attribute` to import the package in isolated process and query its `__path__` attribute.
        try:
            paths = hookutils.get_module_attribute(api.module_name, "__path__")
        except Exception:
            # 007180.python.hook-gi.line36.comment Most likely `gi` cannot be imported.
            paths = []

        for path in paths:
            api.append_package_path(path)
