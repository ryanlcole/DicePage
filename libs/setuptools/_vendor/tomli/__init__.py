# 043302.python.init.line1.comment SPDX-License-Identifier: MIT
# 043303.python.init.line2.comment SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# 043304.python.init.line3.comment Licensed to PSF under a Contributor Agreement.

__all__ = ("loads", "load", "TOMLDecodeError")
__version__ = "2.0.1"  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT

from ._parser import TOMLDecodeError, load, loads

# 043306.python.init.line10.comment Pretend this exception was created here.
TOMLDecodeError.__module__ = __name__
