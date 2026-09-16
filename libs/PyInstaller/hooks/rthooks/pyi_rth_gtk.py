# 008238.python.pyi_rth_gtk.line1.comment -----------------------------------------------------------------------------
# 008239.python.pyi_rth_gtk.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 008240.python.pyi_rth_gtk.line3.comment
# 008241.python.pyi_rth_gtk.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008242.python.pyi_rth_gtk.line5.comment you may not use this file except in compliance with the License.
# 008243.python.pyi_rth_gtk.line6.comment
# 008244.python.pyi_rth_gtk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008245.python.pyi_rth_gtk.line8.comment
# 008246.python.pyi_rth_gtk.line9.comment SPDX-License-Identifier: Apache-2.0
# 008247.python.pyi_rth_gtk.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    os.environ['GTK_DATA_PREFIX'] = sys._MEIPASS
    os.environ['GTK_EXE_PREFIX'] = sys._MEIPASS
    os.environ['GTK_PATH'] = sys._MEIPASS

    # 008248.python.pyi_rth_gtk.line21.comment Include these here, as GTK will import pango automatically.
    os.environ['PANGO_LIBDIR'] = sys._MEIPASS
    os.environ['PANGO_SYSCONFDIR'] = os.path.join(sys._MEIPASS, 'etc')  # TODO?


_pyi_rthook()
del _pyi_rthook
