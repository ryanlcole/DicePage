# 052162.python.common.line1.comment
# 052163.python.common.line2.comment (C) Copyright 2015 Enthought, Inc., Austin, TX
# 052164.python.common.line3.comment All right reserved.
# 052165.python.common.line4.comment
# 052166.python.common.line5.comment This file is open source software distributed according to the terms in
# 052167.python.common.line6.comment LICENSE.txt
# 052168.python.common.line7.comment
from weakref import WeakKeyDictionary

from ._util import ffi

_keep_alive = WeakKeyDictionary()


def _PyBytes_FromStringAndSize(pointer, size):
    buffer = ffi.buffer(pointer, size)
    return buffer[:]


def byreference(x):
    return ffi.new(ffi.getctype(ffi.typeof(x), '*'), x)


def dereference(x):
    return x[0]


def PDWORD(value=0):
    return ffi.new("DWORD *", value)
