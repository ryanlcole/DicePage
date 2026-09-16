# 006632.python.hook-qtpy.line1.comment -----------------------------------------------------------------------------
# 006633.python.hook-qtpy.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006634.python.hook-qtpy.line3.comment
# 006635.python.hook-qtpy.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006636.python.hook-qtpy.line5.comment or later) with exception for distributing the bootloader.
# 006637.python.hook-qtpy.line6.comment
# 006638.python.hook-qtpy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006639.python.hook-qtpy.line8.comment
# 006640.python.hook-qtpy.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006641.python.hook-qtpy.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import qt as qtutils

# 006642.python.hook-qtpy.line14.comment This module conditionally imports all Qt bindings. Prevent all available bindings from being pulled in by trying to
# 006643.python.hook-qtpy.line15.comment select the most applicable one.
# 006644.python.hook-qtpy.line16.comment
# 006645.python.hook-qtpy.line17.comment The preference order for this module appears to be: PyQt5, PySide2, PyQt6, PySide6. See:
# 006646.python.hook-qtpy.line18.comment https://github.com/spyder-ide/qtpy/blob/3238de7a3e038daeb585c1a76fd9a0c4baf22f11/qtpy/__init__.py#L199-L289
# 006647.python.hook-qtpy.line19.comment
# 006648.python.hook-qtpy.line20.comment We, however, use the default preference order of the helper function, in order to keep it consistent across multiple
# 006649.python.hook-qtpy.line21.comment hooks that use the same helper.
excludedimports = qtutils.exclude_extraneous_qt_bindings(
    hook_name="hook-qtpy",
    qt_bindings_order=None,
)
