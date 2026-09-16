# 011500.python.pyi_rth_enchant.line1.comment -----------------------------------------------------------------------------
# 011501.python.pyi_rth_enchant.line2.comment Copyright (c) 2005-2020, PyInstaller Development Team.
# 011502.python.pyi_rth_enchant.line3.comment
# 011503.python.pyi_rth_enchant.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011504.python.pyi_rth_enchant.line5.comment
# 011505.python.pyi_rth_enchant.line6.comment The full license is available in LICENSE, distributed with
# 011506.python.pyi_rth_enchant.line7.comment this software.
# 011507.python.pyi_rth_enchant.line8.comment
# 011508.python.pyi_rth_enchant.line9.comment SPDX-License-Identifier: Apache-2.0
# 011509.python.pyi_rth_enchant.line10.comment -----------------------------------------------------------------------------

import os
import sys

# 011510.python.pyi_rth_enchant.line15.comment On Mac OS X tell enchant library where to look for enchant backends (aspell, myspell, ...).
# 011511.python.pyi_rth_enchant.line16.comment Enchant is looking for backends in directory 'PREFIX/lib/enchant'
# 011512.python.pyi_rth_enchant.line17.comment Note: env. var. ENCHANT_PREFIX_DIR is implemented only in the development version:
# 011513.python.pyi_rth_enchant.line18.comment https://github.com/AbiWord/enchant
# 011514.python.pyi_rth_enchant.line19.comment https://github.com/AbiWord/enchant/pull/2
# 011515.python.pyi_rth_enchant.line20.comment TODO Test this rthook.
if sys.platform.startswith('darwin'):
    os.environ['ENCHANT_PREFIX_DIR'] = os.path.join(sys._MEIPASS, 'enchant')
