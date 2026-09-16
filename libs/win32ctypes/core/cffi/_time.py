# 052199.python.time.line1.comment
# 052200.python.time.line2.comment (C) Copyright 2015-18 Enthought, Inc., Austin, TX
# 052201.python.time.line3.comment All right reserved.
# 052202.python.time.line4.comment
# 052203.python.time.line5.comment This file is open source software distributed according to the terms in
# 052204.python.time.line6.comment LICENSE.txt
# 052205.python.time.line7.comment
from ._util import ffi, dlls

ffi.cdef("""

DWORD WINAPI GetTickCount(void);

""")


def _GetTickCount():
    return dlls.kernel32.GetTickCount()
