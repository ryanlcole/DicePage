# 008189.python.pyi_rth_gi.line1.comment -----------------------------------------------------------------------------
# 008190.python.pyi_rth_gi.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 008191.python.pyi_rth_gi.line3.comment
# 008192.python.pyi_rth_gi.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008193.python.pyi_rth_gi.line5.comment you may not use this file except in compliance with the License.
# 008194.python.pyi_rth_gi.line6.comment
# 008195.python.pyi_rth_gi.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008196.python.pyi_rth_gi.line8.comment
# 008197.python.pyi_rth_gi.line9.comment SPDX-License-Identifier: Apache-2.0
# 008198.python.pyi_rth_gi.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    os.environ['GI_TYPELIB_PATH'] = os.path.join(sys._MEIPASS, 'gi_typelibs')


_pyi_rthook()
del _pyi_rthook
