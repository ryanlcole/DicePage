# 008109.python.hook-urllib3.packages.six.moves.line1.comment -----------------------------------------------------------------------------
# 008110.python.hook-urllib3.packages.six.moves.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008111.python.hook-urllib3.packages.six.moves.line3.comment
# 008112.python.hook-urllib3.packages.six.moves.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008113.python.hook-urllib3.packages.six.moves.line5.comment or later) with exception for distributing the bootloader.
# 008114.python.hook-urllib3.packages.six.moves.line6.comment
# 008115.python.hook-urllib3.packages.six.moves.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008116.python.hook-urllib3.packages.six.moves.line8.comment
# 008117.python.hook-urllib3.packages.six.moves.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 008118.python.hook-urllib3.packages.six.moves.line10.comment -----------------------------------------------------------------------------

from PyInstaller import isolated

# 008119.python.hook-urllib3.packages.six.moves.line14.comment This basically is a copy of pre_safe_import_module/hook-six.moves.py adopted to urllib3.packages.six. Please see
# 008120.python.hook-urllib3.packages.six.moves.line15.comment pre_safe_import_module/hook-six.moves.py for documentation.


def pre_safe_import_module(api):
    @isolated.call
    def real_to_six_module_name():
        try:
            import urllib3.packages.six as six
        except ImportError:
            return None  # unavailable

        return {
            moved.mod: 'urllib3.packages.six.moves.' + moved.name
            for moved in six._moved_attributes if isinstance(moved, (six.MovedModule, six.MovedAttribute))
        }

    if real_to_six_module_name is not None:
        api.add_runtime_package(api.module_name)
        for real_module_name, six_module_name in real_to_six_module_name.items():
            api.add_alias_module(real_module_name, six_module_name)
