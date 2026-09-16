# 052310.python.pywintypes.line1.comment
# 052311.python.pywintypes.line2.comment (C) Copyright 2017 Enthought, Inc., Austin, TX
# 052312.python.pywintypes.line3.comment All right reserved.
# 052313.python.pywintypes.line4.comment
# 052314.python.pywintypes.line5.comment This file is open source software distributed according to the terms in
# 052315.python.pywintypes.line6.comment LICENSE.txt
# 052316.python.pywintypes.line7.comment
import warnings
from win32ctypes.pywin32.pywintypes import *  # noqa

warnings.warn(
    "Please use 'from win32ctypes.pywin32 import pywintypes'",
    DeprecationWarning)
