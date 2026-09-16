# 052176.python.nl_support.line1.comment
# 052177.python.nl_support.line2.comment (C) Copyright 2015-18 Enthought, Inc., Austin, TX
# 052178.python.nl_support.line3.comment All right reserved.
# 052179.python.nl_support.line4.comment
# 052180.python.nl_support.line5.comment This file is open source software distributed according to the terms in
# 052181.python.nl_support.line6.comment LICENSE.txt
# 052182.python.nl_support.line7.comment
from ._util import ffi, dlls

ffi.cdef("""

UINT WINAPI GetACP(void);

""")


def _GetACP():
    return dlls.kernel32.GetACP()
