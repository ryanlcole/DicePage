# 052238.python.dll.line1.comment
# 052239.python.dll.line2.comment (C) Copyright 2018 Enthought, Inc., Austin, TX
# 052240.python.dll.line3.comment All right reserved.
# 052241.python.dll.line4.comment
# 052242.python.dll.line5.comment This file is open source software distributed according to the terms in
# 052243.python.dll.line6.comment LICENSE.txt
# 052244.python.dll.line7.comment
from ctypes.wintypes import BOOL, DWORD, HANDLE, HMODULE, LPCWSTR

from ._util import check_null, check_false, function_factory, dlls

_LoadLibraryEx = function_factory(
    dlls.kernel32.LoadLibraryExW,
    [LPCWSTR, HANDLE, DWORD],
    HMODULE, check_null)

_FreeLibrary = function_factory(
    dlls.kernel32.FreeLibrary,
    [HMODULE],
    BOOL,
    check_false)
