# 008305.python.pyi_rth_kivy.line1.comment -----------------------------------------------------------------------------
# 008306.python.pyi_rth_kivy.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 008307.python.pyi_rth_kivy.line3.comment
# 008308.python.pyi_rth_kivy.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008309.python.pyi_rth_kivy.line5.comment you may not use this file except in compliance with the License.
# 008310.python.pyi_rth_kivy.line6.comment
# 008311.python.pyi_rth_kivy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008312.python.pyi_rth_kivy.line8.comment
# 008313.python.pyi_rth_kivy.line9.comment SPDX-License-Identifier: Apache-2.0
# 008314.python.pyi_rth_kivy.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    root = os.path.join(sys._MEIPASS, 'kivy_install')

    os.environ['KIVY_DATA_DIR'] = os.path.join(root, 'data')
    os.environ['KIVY_MODULES_DIR'] = os.path.join(root, 'modules')


_pyi_rthook()
del _pyi_rthook
