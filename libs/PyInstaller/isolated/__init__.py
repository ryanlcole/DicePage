# 008584.python.init.line1.comment -----------------------------------------------------------------------------
# 008585.python.init.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 008586.python.init.line3.comment
# 008587.python.init.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008588.python.init.line5.comment or later) or, at the user's discretion, the MIT License.
# 008589.python.init.line6.comment
# 008590.python.init.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008591.python.init.line8.comment
# 008592.python.init.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception OR MIT)
# 008593.python.init.line10.comment -----------------------------------------------------------------------------
"""
PyInstaller hooks typically will need to import the package which they are written for but doing so may manipulate
globals such as :data:`sys.path` or :data:`os.environ` in ways that affect the build. For example, on Windows,
Qt's binaries are added to then loaded via ``PATH`` in such a way that if you import multiple Qt variants in one
session then there is no guarantee which variant's binaries each variant will get!

To get around this, PyInstaller does any such tasks in an isolated Python subprocess and ships a
:mod:`PyInstaller.isolated` submodule to do so in hooks. ::

    from PyInstaller import isolated

This submodule provides:

*   :func:`isolated.call() <call>` to evaluate functions in isolation.
*   :func:`@isolated.decorate <decorate>` to mark a function as always called in isolation.
*   :class:`isolated.Python() <Python>` to efficiently call many functions in a single child instance of Python.

"""

# 008594.python.init.line30.comment flake8: noqa
from ._parent import Python, call, decorate, SubprocessDiedError
