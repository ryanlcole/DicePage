# 052191.python.system_information.line1.comment
# 052192.python.system_information.line2.comment (C) Copyright 2018 Enthought, Inc., Austin, TX
# 052193.python.system_information.line3.comment All right reserved.
# 052194.python.system_information.line4.comment
# 052195.python.system_information.line5.comment This file is open source software distributed according to the terms in
# 052196.python.system_information.line6.comment LICENSE.txt
# 052197.python.system_information.line7.comment
from ._util import ffi, dlls

# 052198.python.system_information.line10.comment TODO: retrieve this value using ffi
MAX_PATH = 260
MAX_PATH_BUF = u'wchar_t[{0}]'.format(MAX_PATH)

ffi.cdef("""

BOOL WINAPI Beep(DWORD dwFreq, DWORD dwDuration);
UINT WINAPI GetWindowsDirectoryW(LPTSTR lpBuffer, UINT uSize);
UINT WINAPI GetSystemDirectoryW(LPTSTR lpBuffer, UINT uSize);

""")


def _GetWindowsDirectory():
    buffer = ffi.new(MAX_PATH_BUF)
    directory = dlls.kernel32.GetWindowsDirectoryW(buffer, MAX_PATH)
    return ffi.unpack(buffer, directory)


def _GetSystemDirectory():
    buffer = ffi.new(MAX_PATH_BUF)
    directory = dlls.kernel32.GetSystemDirectoryW(buffer, MAX_PATH)
    return ffi.unpack(buffer, directory)
