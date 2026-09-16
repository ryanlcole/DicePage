# 006341.python.hook-matplotlib.backends.qt_compat.line1.comment -----------------------------------------------------------------------------
# 006342.python.hook-matplotlib.backends.qt_compat.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006343.python.hook-matplotlib.backends.qt_compat.line3.comment
# 006344.python.hook-matplotlib.backends.qt_compat.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006345.python.hook-matplotlib.backends.qt_compat.line5.comment or later) with exception for distributing the bootloader.
# 006346.python.hook-matplotlib.backends.qt_compat.line6.comment
# 006347.python.hook-matplotlib.backends.qt_compat.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006348.python.hook-matplotlib.backends.qt_compat.line8.comment
# 006349.python.hook-matplotlib.backends.qt_compat.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006350.python.hook-matplotlib.backends.qt_compat.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import qt as qtutils

# 006351.python.hook-matplotlib.backends.qt_compat.line14.comment This module conditionally imports all Qt bindings. Prevent all available bindings from being pulled in by trying to
# 006352.python.hook-matplotlib.backends.qt_compat.line15.comment select the most applicable one.
# 006353.python.hook-matplotlib.backends.qt_compat.line16.comment
# 006354.python.hook-matplotlib.backends.qt_compat.line17.comment The preference order for this module appears to be: PyQt6, PySide6, PyQt5, PySide2 (or just PyQt5, PySide2 if Qt5
# 006355.python.hook-matplotlib.backends.qt_compat.line18.comment bindings are forced). See:
# 006356.python.hook-matplotlib.backends.qt_compat.line19.comment https://github.com/matplotlib/matplotlib/blob/9e18a343fb58a2978a8e27df03190ed21c61c343/lib/matplotlib/backends/qt_compat.py#L113-L125
# 006357.python.hook-matplotlib.backends.qt_compat.line20.comment
# 006358.python.hook-matplotlib.backends.qt_compat.line21.comment We, however, use the default preference order of the helper function, in order to keep it consistent across multiple
# 006359.python.hook-matplotlib.backends.qt_compat.line22.comment hooks that use the same helper.
excludedimports = qtutils.exclude_extraneous_qt_bindings(
    hook_name="hook-matplotlib.backends.qt_compat",
    qt_bindings_order=None,
)
