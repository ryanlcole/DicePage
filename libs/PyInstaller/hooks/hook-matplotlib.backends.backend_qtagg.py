# 006260.python.hook-matplotlib.backends.backend_qtagg.line1.comment -----------------------------------------------------------------------------
# 006261.python.hook-matplotlib.backends.backend_qtagg.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006262.python.hook-matplotlib.backends.backend_qtagg.line3.comment
# 006263.python.hook-matplotlib.backends.backend_qtagg.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006264.python.hook-matplotlib.backends.backend_qtagg.line5.comment or later) with exception for distributing the bootloader.
# 006265.python.hook-matplotlib.backends.backend_qtagg.line6.comment
# 006266.python.hook-matplotlib.backends.backend_qtagg.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006267.python.hook-matplotlib.backends.backend_qtagg.line8.comment
# 006268.python.hook-matplotlib.backends.backend_qtagg.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006269.python.hook-matplotlib.backends.backend_qtagg.line10.comment -----------------------------------------------------------------------------

# 006270.python.hook-matplotlib.backends.backend_qtagg.line12.comment This module conditionally imports PyQt6:
# 006271.python.hook-matplotlib.backends.backend_qtagg.line13.comment https://github.com/matplotlib/matplotlib/blob/9e18a343fb58a2978a8e27df03190ed21c61c343/lib/matplotlib/backends/backend_qtagg.py#L52-L53
# 006272.python.hook-matplotlib.backends.backend_qtagg.line14.comment Suppress this import to prevent PyQt6 from being accidentally pulled in; the actually relevant Qt bindings are
# 006273.python.hook-matplotlib.backends.backend_qtagg.line15.comment determined by our hook for `matplotlib.backends.qt_compat` module.
excludedimports = ['PyQt6']
