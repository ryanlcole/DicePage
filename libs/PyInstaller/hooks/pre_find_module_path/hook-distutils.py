# 007060.python.hook-distutils.line1.comment -----------------------------------------------------------------------------
# 007061.python.hook-distutils.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007062.python.hook-distutils.line3.comment
# 007063.python.hook-distutils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007064.python.hook-distutils.line5.comment or later) with exception for distributing the bootloader.
# 007065.python.hook-distutils.line6.comment
# 007066.python.hook-distutils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007067.python.hook-distutils.line8.comment
# 007068.python.hook-distutils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007069.python.hook-distutils.line10.comment -----------------------------------------------------------------------------
"""
`distutils`-specific pre-find module path hook.

When run from within a virtual environment, this hook changes the `__path__` of the `distutils` package to
that of the system-wide rather than virtual-environment-specific `distutils` package. While the former is suitable for
freezing, the latter is intended for use _only_ from within virtual environments.

NOTE: this behavior seems to be specific to virtual environments created by (an old?) version of `virtualenv`; it is not
applicable to virtual environments created by the `venv`.
"""

import pathlib

from PyInstaller.utils.hooks import logger, get_module_file_attribute


def pre_find_module_path(api):
    # 007070.python.hook-distutils.line28.comment Absolute path of the system-wide "distutils" package when run from within a venv or None otherwise.

    # 007071.python.hook-distutils.line30.comment opcode is not a virtualenv module, so we can use it to find the stdlib. Technique taken from virtualenv's
    # 007072.python.hook-distutils.line31.comment "distutils" package detection at
    # 007073.python.hook-distutils.line32.comment https://github.com/pypa/virtualenv/blob/16.3.0/virtualenv_embedded/distutils-init.py#L5
    # 007074.python.hook-distutils.line33.comment As opcode is a module, stdlib path corresponds to the parent directory of its ``__file__`` attribute.
    stdlib_path = pathlib.Path(get_module_file_attribute('opcode')).parent.resolve()
    # 007075.python.hook-distutils.line35.comment As distutils is a package, we need to consider the grandparent directory of its ``__file__`` attribute.
    distutils_path = pathlib.Path(get_module_file_attribute('distutils')).parent.parent.resolve()

    if distutils_path.name == 'setuptools':
        logger.debug("distutils: provided by setuptools")
    elif distutils_path == stdlib_path:
        logger.debug("distutils: provided by stdlib")
    else:
        # 007076.python.hook-distutils.line43.comment Find this package in stdlib.
        stdlib_path = str(stdlib_path)
        logger.debug("distutils: virtualenv shim - retargeting to stdlib dir %r", stdlib_path)
        api.search_dirs = [stdlib_path]
