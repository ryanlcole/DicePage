# 052266.python.time.line1.comment
# 052267.python.time.line2.comment (C) Copyright 2018 Enthought, Inc., Austin, TX
# 052268.python.time.line3.comment All right reserved.
# 052269.python.time.line4.comment
# 052270.python.time.line5.comment This file is open source software distributed according to the terms in
# 052271.python.time.line6.comment LICENSE.txt
# 052272.python.time.line7.comment
from ctypes.wintypes import DWORD

from ._util import function_factory, dlls


_GetTickCount = function_factory(
    dlls.kernel32.GetTickCount,
    None, DWORD)
