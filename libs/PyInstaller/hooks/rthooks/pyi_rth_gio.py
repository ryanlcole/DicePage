# 008199.python.pyi_rth_gio.line1.comment -----------------------------------------------------------------------------
# 008200.python.pyi_rth_gio.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 008201.python.pyi_rth_gio.line3.comment
# 008202.python.pyi_rth_gio.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008203.python.pyi_rth_gio.line5.comment you may not use this file except in compliance with the License.
# 008204.python.pyi_rth_gio.line6.comment
# 008205.python.pyi_rth_gio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008206.python.pyi_rth_gio.line8.comment
# 008207.python.pyi_rth_gio.line9.comment SPDX-License-Identifier: Apache-2.0
# 008208.python.pyi_rth_gio.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    os.environ['GIO_MODULE_DIR'] = os.path.join(sys._MEIPASS, 'gio_modules')


_pyi_rthook()
del _pyi_rthook
