# 052169.python.dll.line1.comment
# 052170.python.dll.line2.comment (C) Copyright 2018 Enthought, Inc., Austin, TX
# 052171.python.dll.line3.comment All right reserved.
# 052172.python.dll.line4.comment
# 052173.python.dll.line5.comment This file is open source software distributed according to the terms in
# 052174.python.dll.line6.comment LICENSE.txt
# 052175.python.dll.line7.comment
from ._util import ffi, check_null, check_false, dlls, HMODULE, PVOID


ffi.cdef("""

HMODULE WINAPI LoadLibraryExW(LPCTSTR lpFileName, HANDLE hFile, DWORD dwFlags);
BOOL WINAPI FreeLibrary(HMODULE hModule);

""")


def _LoadLibraryEx(lpFilename, hFile, dwFlags):
    result = check_null(
        dlls.kernel32.LoadLibraryExW(
            str(lpFilename), ffi.NULL, dwFlags),
        function_name='LoadLibraryEx')
    return HMODULE(result)


def _FreeLibrary(hModule):
    check_false(
        dlls.kernel32.FreeLibrary(PVOID(hModule)),
        function_name='FreeLibrary')
