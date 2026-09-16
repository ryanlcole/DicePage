# 008029.python.hook-setuptools.extern.six.moves.line1.comment -----------------------------------------------------------------------------
# 008030.python.hook-setuptools.extern.six.moves.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008031.python.hook-setuptools.extern.six.moves.line3.comment
# 008032.python.hook-setuptools.extern.six.moves.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008033.python.hook-setuptools.extern.six.moves.line5.comment or later) with exception for distributing the bootloader.
# 008034.python.hook-setuptools.extern.six.moves.line6.comment
# 008035.python.hook-setuptools.extern.six.moves.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008036.python.hook-setuptools.extern.six.moves.line8.comment
# 008037.python.hook-setuptools.extern.six.moves.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008038.python.hook-setuptools.extern.six.moves.line10.comment -----------------------------------------------------------------------------

from PyInstaller import isolated

# 008039.python.hook-setuptools.extern.six.moves.line14.comment This is basically a copy of pre_safe_import_module/hook-six.moves.py adopted to setuptools.extern.six resp.
# 008040.python.hook-setuptools.extern.six.moves.line15.comment setuptools._vendor.six. Please see pre_safe_import_module/hook-six.moves.py for documentation.

# 008041.python.hook-setuptools.extern.six.moves.line17.comment Note that the moves are defined in 'setuptools._vendor.six' but are imported under 'setuptools.extern.six'.


def pre_safe_import_module(api):
    @isolated.call
    def real_to_six_module_name():
        try:
            import setuptools._vendor.six as six
        except ImportError:
            try:
                import setuptools.extern.six as six
            except ImportError:
                return None  # unavailable

        return {
            moved.mod: 'setuptools.extern.six.moves.' + moved.name
            for moved in six._moved_attributes if isinstance(moved, (six.MovedModule, six.MovedAttribute))
        }

    if real_to_six_module_name is not None:
        api.add_runtime_package(api.module_name)
        for real_module_name, six_module_name in real_to_six_module_name.items():
            api.add_alias_module(real_module_name, six_module_name)
