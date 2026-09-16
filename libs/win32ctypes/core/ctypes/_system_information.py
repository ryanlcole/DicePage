# 052259.python.system_information.line1.comment
# 052260.python.system_information.line2.comment (C) Copyright 2018 Enthought, Inc., Austin, TX
# 052261.python.system_information.line3.comment All right reserved.
# 052262.python.system_information.line4.comment
# 052263.python.system_information.line5.comment This file is open source software distributed according to the terms in
# 052264.python.system_information.line6.comment LICENSE.txt
# 052265.python.system_information.line7.comment
import ctypes
from ctypes.wintypes import LPCWSTR, UINT, LPWSTR, MAX_PATH

from ._util import check_zero, function_factory, dlls


def _GetWindowsDirectory():
    buffer = ctypes.create_unicode_buffer(MAX_PATH)
    _BaseGetWindowsDirectory(buffer, MAX_PATH)
    return ctypes.cast(buffer, LPCWSTR).value


def _GetSystemDirectory():
    buffer = ctypes.create_unicode_buffer(MAX_PATH)
    _BaseGetSystemDirectory(buffer, MAX_PATH)
    return ctypes.cast(buffer, LPCWSTR).value


_BaseGetWindowsDirectory = function_factory(
    dlls.kernel32.GetWindowsDirectoryW,
    [LPWSTR, UINT],
    UINT,
    check_zero)

_BaseGetSystemDirectory = function_factory(
    dlls.kernel32.GetSystemDirectoryW,
    [LPWSTR, UINT],
    UINT,
    check_zero)
