# 019996.python.hook-vtkpython.line1.comment ------------------------------------------------------------------
# 019997.python.hook-vtkpython.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 019998.python.hook-vtkpython.line3.comment
# 019999.python.hook-vtkpython.line4.comment This file is distributed under the terms of the GNU General Public
# 020000.python.hook-vtkpython.line5.comment License (version 2.0 or later).
# 020001.python.hook-vtkpython.line6.comment
# 020002.python.hook-vtkpython.line7.comment The full license is available in LICENSE, distributed with
# 020003.python.hook-vtkpython.line8.comment this software.
# 020004.python.hook-vtkpython.line9.comment
# 020005.python.hook-vtkpython.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020006.python.hook-vtkpython.line11.comment ------------------------------------------------------------------

import os
if os.name == 'posix':
    hiddenimports = [
        'libvtkCommonPython', 'libvtkFilteringPython', 'libvtkIOPython',
        'libvtkImagingPython', 'libvtkGraphicsPython', 'libvtkRenderingPython',
        'libvtkHybridPython', 'libvtkParallelPython', 'libvtkPatentedPython'
    ]
else:
    hiddenimports = [
        'vtkCommonPython', 'vtkFilteringPython', 'vtkIOPython',
        'vtkImagingPython', 'vtkGraphicsPython', 'vtkRenderingPython',
        'vtkHybridPython', 'vtkParallelPython', 'vtkPatentedPython'
    ]
