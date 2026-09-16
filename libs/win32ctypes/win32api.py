# 052411.python.win32api.line1.comment
# 052412.python.win32api.line2.comment (C) Copyright 2014 Enthought, Inc., Austin, TX
# 052413.python.win32api.line3.comment All right reserved.
# 052414.python.win32api.line4.comment
# 052415.python.win32api.line5.comment This file is open source software distributed according to the terms in
# 052416.python.win32api.line6.comment LICENSE.txt
# 052417.python.win32api.line7.comment
import warnings
from win32ctypes.pywin32.win32api import *  # noqa

warnings.warn(
    "Please use 'from win32ctypes.pywin32 import win32api'",
    DeprecationWarning)
