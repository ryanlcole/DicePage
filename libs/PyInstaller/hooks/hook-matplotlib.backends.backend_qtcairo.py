# 006274.python.hook-matplotlib.backends.backend_qtcairo.line1.comment -----------------------------------------------------------------------------
# 006275.python.hook-matplotlib.backends.backend_qtcairo.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006276.python.hook-matplotlib.backends.backend_qtcairo.line3.comment
# 006277.python.hook-matplotlib.backends.backend_qtcairo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006278.python.hook-matplotlib.backends.backend_qtcairo.line5.comment or later) with exception for distributing the bootloader.
# 006279.python.hook-matplotlib.backends.backend_qtcairo.line6.comment
# 006280.python.hook-matplotlib.backends.backend_qtcairo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006281.python.hook-matplotlib.backends.backend_qtcairo.line8.comment
# 006282.python.hook-matplotlib.backends.backend_qtcairo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006283.python.hook-matplotlib.backends.backend_qtcairo.line10.comment -----------------------------------------------------------------------------

# 006284.python.hook-matplotlib.backends.backend_qtcairo.line12.comment This module conditionally imports PyQt6:
# 006285.python.hook-matplotlib.backends.backend_qtcairo.line13.comment https://github.com/matplotlib/matplotlib/blob/9e18a343fb58a2978a8e27df03190ed21c61c343/lib/matplotlib/backends/backend_qtcairo.py#L24-L25
# 006286.python.hook-matplotlib.backends.backend_qtcairo.line14.comment Suppress this import to prevent PyQt6 from being accidentally pulled in; the actually relevant Qt bindings are
# 006287.python.hook-matplotlib.backends.backend_qtcairo.line15.comment determined by our hook for `matplotlib.backends.qt_compat` module.
excludedimports = ['PyQt6']
