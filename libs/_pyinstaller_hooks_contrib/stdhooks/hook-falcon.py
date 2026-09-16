# 013329.python.hook-falcon.line1.comment ------------------------------------------------------------------
# 013330.python.hook-falcon.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 013331.python.hook-falcon.line3.comment
# 013332.python.hook-falcon.line4.comment This file is distributed under the terms of the GNU General Public
# 013333.python.hook-falcon.line5.comment License (version 2.0 or later).
# 013334.python.hook-falcon.line6.comment
# 013335.python.hook-falcon.line7.comment The full license is available in LICENSE, distributed with
# 013336.python.hook-falcon.line8.comment this software.
# 013337.python.hook-falcon.line9.comment
# 013338.python.hook-falcon.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013339.python.hook-falcon.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_py311
from PyInstaller.utils.hooks import is_module_satisfies

hiddenimports = [
    'cgi',
    'falcon.app_helpers',
    'falcon.forwarded',
    'falcon.media',
    'falcon.request_helpers',
    'falcon.responders',
    'falcon.response_helpers',
    'falcon.routing',
    'falcon.vendor.mimeparse',
    'falcon.vendor',
    'uuid',
    'xml.etree.ElementTree',
    'xml.etree'
]

# 013340.python.hook-falcon.line32.comment falcon v4.0.0 added couple of more cythonized modules that depend on the following stdlib modules.
if is_module_satisfies('falcon >= 4.0.0'):
    hiddenimports += [
        'dataclasses',
        'json',
    ]

    # 013341.python.hook-falcon.line39.comment `wsgiref.types` is available (and thus referenced) only under python >= 3.11.
    if is_py311:
        hiddenimports += ['wsgiref.types']
