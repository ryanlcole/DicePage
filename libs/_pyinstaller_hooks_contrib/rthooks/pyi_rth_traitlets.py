# 011681.python.pyi_rth_traitlets.line1.comment -----------------------------------------------------------------------------
# 011682.python.pyi_rth_traitlets.line2.comment Copyright (c) 2005-2020, PyInstaller Development Team.
# 011683.python.pyi_rth_traitlets.line3.comment
# 011684.python.pyi_rth_traitlets.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011685.python.pyi_rth_traitlets.line5.comment
# 011686.python.pyi_rth_traitlets.line6.comment The full license is available in LICENSE, distributed with
# 011687.python.pyi_rth_traitlets.line7.comment this software.
# 011688.python.pyi_rth_traitlets.line8.comment
# 011689.python.pyi_rth_traitlets.line9.comment SPDX-License-Identifier: Apache-2.0
# 011690.python.pyi_rth_traitlets.line10.comment -----------------------------------------------------------------------------

# 011691.python.pyi_rth_traitlets.line12.comment 'traitlets' uses module 'inspect' from default Python library to inspect
# 011692.python.pyi_rth_traitlets.line13.comment source code of modules. However, frozen app does not contain source code
# 011693.python.pyi_rth_traitlets.line14.comment of Python modules.
# 011694.python.pyi_rth_traitlets.line15.comment
# 011695.python.pyi_rth_traitlets.line16.comment hook-IPython depends on module 'traitlets'.

import traitlets.traitlets


def _disabled_deprecation_warnings(method, cls, method_name, msg):
    pass


traitlets.traitlets._deprecated_method = _disabled_deprecation_warnings
