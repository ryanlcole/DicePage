# 052419.python.win32cred.line1.comment
# 052420.python.win32cred.line2.comment (C) Copyright 2014 Enthought, Inc., Austin, TX
# 052421.python.win32cred.line3.comment All right reserved.
# 052422.python.win32cred.line4.comment
# 052423.python.win32cred.line5.comment This file is open source software distributed according to the terms in
# 052424.python.win32cred.line6.comment LICENSE.txt
# 052425.python.win32cred.line7.comment
import warnings
from win32ctypes.pywin32.win32cred import *  # noqa

warnings.warn(
    "Please use 'from win32ctypes.pywin32 import win32cred'",
    DeprecationWarning)
