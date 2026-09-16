# 052245.python.nl_support.line1.comment
# 052246.python.nl_support.line2.comment (C) Copyright 2018 Enthought, Inc., Austin, TX
# 052247.python.nl_support.line3.comment All right reserved.
# 052248.python.nl_support.line4.comment
# 052249.python.nl_support.line5.comment This file is open source software distributed according to the terms in
# 052250.python.nl_support.line6.comment LICENSE.txt
# 052251.python.nl_support.line7.comment
from ctypes.wintypes import UINT

from ._util import function_factory, dlls

_GetACP = function_factory(dlls.kernel32.GetACP, None, UINT)
