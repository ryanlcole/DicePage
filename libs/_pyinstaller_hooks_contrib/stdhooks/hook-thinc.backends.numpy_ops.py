# 017480.python.hook-thinc.backends.numpy_ops.line1.comment ------------------------------------------------------------------
# 017481.python.hook-thinc.backends.numpy_ops.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 017482.python.hook-thinc.backends.numpy_ops.line3.comment
# 017483.python.hook-thinc.backends.numpy_ops.line4.comment This file is distributed under the terms of the GNU General Public
# 017484.python.hook-thinc.backends.numpy_ops.line5.comment License (version 2.0 or later).
# 017485.python.hook-thinc.backends.numpy_ops.line6.comment
# 017486.python.hook-thinc.backends.numpy_ops.line7.comment The full license is available in LICENSE, distributed with
# 017487.python.hook-thinc.backends.numpy_ops.line8.comment this software.
# 017488.python.hook-thinc.backends.numpy_ops.line9.comment
# 017489.python.hook-thinc.backends.numpy_ops.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017490.python.hook-thinc.backends.numpy_ops.line11.comment ------------------------------------------------------------------
"""
thinc.banckends.numpy_ops contains hidden imports which are needed to import it
This hook was created to make spacy work correctly.
"""

hiddenimports = ['cymem.cymem', 'preshed.maps', 'blis.py']
