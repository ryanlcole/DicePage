# 011292.python.winutils.line1.comment -----------------------------------------------------------------------------
# 011293.python.winutils.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 011294.python.winutils.line3.comment
# 011295.python.winutils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 011296.python.winutils.line5.comment or later) with exception for distributing the bootloader.
# 011297.python.winutils.line6.comment
# 011298.python.winutils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 011299.python.winutils.line8.comment
# 011300.python.winutils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 011301.python.winutils.line10.comment -----------------------------------------------------------------------------
"""
Utilities for Windows platform.
"""

from PyInstaller import compat


def get_windows_dir():
    """
    Return the Windows directory, e.g., C:\\Windows.
    """
    windir = compat.win32api.GetWindowsDirectory()
    if not windir:
        raise SystemExit("ERROR: Cannot determine Windows directory!")
    return windir


def get_system_path():
    """
    Return the required Windows system paths.
    """
    sys_dir = compat.win32api.GetSystemDirectory()
    # 011302.python.winutils.line33.comment Ensure C:\Windows\system32  and C:\Windows directories are always present in PATH variable.
    # 011303.python.winutils.line34.comment C:\Windows\system32 is valid even for 64-bit Windows. Access do DLLs are transparently redirected to
    # 011304.python.winutils.line35.comment C:\Windows\syswow64 for 64bit applactions.
    # 011305.python.winutils.line36.comment See http://msdn.microsoft.com/en-us/library/aa384187(v=vs.85).aspx
    return [sys_dir, get_windows_dir()]


def get_pe_file_machine_type(filename):
    """
    Return the machine type code from the header of the given PE file.
    """
    import pefile

    with pefile.PE(filename, fast_load=True) as pe:
        return pe.FILE_HEADER.Machine


def set_exe_build_timestamp(exe_path, timestamp):
    """
    Modifies the executable's build timestamp by updating values in the corresponding PE headers.
    """
    import pefile

    with pefile.PE(exe_path, fast_load=True) as pe:
        # 011306.python.winutils.line57.comment Manually perform a full load. We need it to load all headers, but specifying it in the constructor triggers
        # 011307.python.winutils.line58.comment byte statistics gathering that takes forever with large files. So we try to go around that...
        pe.full_load()

        # 011308.python.winutils.line61.comment Set build timestamp.
        # 011309.python.winutils.line62.comment See: https://0xc0decafe.com/malware-analyst-guide-to-pe-timestamps
        timestamp = int(timestamp)
        # 011310.python.winutils.line64.comment Set timestamp field in FILE_HEADER
        pe.FILE_HEADER.TimeDateStamp = timestamp
        # 011311.python.winutils.line66.comment MSVC-compiled executables contain (at least?) one DIRECTORY_ENTRY_DEBUG entry that also contains timestamp
        # 011312.python.winutils.line67.comment with same value as set in FILE_HEADER. So modify that as well, as long as it is set.
        debug_entries = getattr(pe, 'DIRECTORY_ENTRY_DEBUG', [])
        for debug_entry in debug_entries:
            if debug_entry.struct.TimeDateStamp:
                debug_entry.struct.TimeDateStamp = timestamp

        # 011313.python.winutils.line73.comment Generate updated EXE data
        data = pe.write()

    # 011314.python.winutils.line76.comment Rewrite the exe
    with open(exe_path, 'wb') as fp:
        fp.write(data)


def update_exe_pe_checksum(exe_path):
    """
    Compute the executable's PE checksum, and write it to PE headers.

    This optional checksum is supposed to protect the executable against corruption but some anti-viral software have
    taken to flagging anything without it set correctly as malware. See issue #5579.
    """
    import pefile

    # 011315.python.winutils.line90.comment Compute checksum using our equivalent of the MapFileAndCheckSumW - for large files, it is significantly faster
    # 011316.python.winutils.line91.comment than pure-pyton pefile.PE.generate_checksum(). However, it requires the file to be on disk (i.e., cannot operate
    # 011317.python.winutils.line92.comment on a memory buffer).
    try:
        checksum = compute_exe_pe_checksum(exe_path)
    except Exception as e:
        raise RuntimeError("Failed to compute PE checksum!") from e

    # 011318.python.winutils.line98.comment Update the checksum
    with pefile.PE(exe_path, fast_load=True) as pe:
        pe.OPTIONAL_HEADER.CheckSum = checksum

        # 011319.python.winutils.line102.comment Generate updated EXE data
        data = pe.write()

    # 011320.python.winutils.line105.comment Rewrite the exe
    with open(exe_path, 'wb') as fp:
        fp.write(data)


def compute_exe_pe_checksum(exe_path):
    """
    This is a replacement for the MapFileAndCheckSumW function. As noted in MSDN documentation, the Microsoft's
    implementation of MapFileAndCheckSumW internally calls its ASCII variant (MapFileAndCheckSumA), and therefore
    cannot handle paths that contain characters that are not representable in the current code page.
    See: https://docs.microsoft.com/en-us/windows/win32/api/imagehlp/nf-imagehlp-mapfileandchecksumw

    This function is based on Wine's implementation of MapFileAndCheckSumW, and due to being based entirely on
    the pure widechar-API functions, it is not limited by the current code page.
    """
    # 011321.python.winutils.line120.comment ctypes bindings for relevant win32 API functions
    import ctypes
    from ctypes import windll, wintypes

    INVALID_HANDLE = wintypes.HANDLE(-1).value

    GetLastError = ctypes.windll.kernel32.GetLastError
    GetLastError.argtypes = ()
    GetLastError.restype = wintypes.DWORD

    CloseHandle = windll.kernel32.CloseHandle
    CloseHandle.argtypes = (
        wintypes.HANDLE,  # hObject
    )
    CloseHandle.restype = wintypes.BOOL

    CreateFileW = windll.kernel32.CreateFileW
    CreateFileW.argtypes = (
        wintypes.LPCWSTR,  # lpFileName
        wintypes.DWORD,  # dwDesiredAccess
        wintypes.DWORD,  # dwShareMode
        wintypes.LPVOID,  # lpSecurityAttributes
        wintypes.DWORD,  # dwCreationDisposition
        wintypes.DWORD,  # dwFlagsAndAttributes
        wintypes.HANDLE,  # hTemplateFile
    )
    CreateFileW.restype = wintypes.HANDLE

    CreateFileMappingW = windll.kernel32.CreateFileMappingW
    CreateFileMappingW.argtypes = (
        wintypes.HANDLE,  # hFile
        wintypes.LPVOID,  # lpSecurityAttributes
        wintypes.DWORD,  # flProtect
        wintypes.DWORD,  # dwMaximumSizeHigh
        wintypes.DWORD,  # dwMaximumSizeLow
        wintypes.LPCWSTR,  # lpName
    )
    CreateFileMappingW.restype = wintypes.HANDLE

    MapViewOfFile = windll.kernel32.MapViewOfFile
    MapViewOfFile.argtypes = (
        wintypes.HANDLE,  # hFileMappingObject
        wintypes.DWORD,  # dwDesiredAccess
        wintypes.DWORD,  # dwFileOffsetHigh
        wintypes.DWORD,  # dwFileOffsetLow
        wintypes.DWORD,  # dwNumberOfBytesToMap
    )
    MapViewOfFile.restype = wintypes.LPVOID

    UnmapViewOfFile = windll.kernel32.UnmapViewOfFile
    UnmapViewOfFile.argtypes = (
        wintypes.LPCVOID,  # lpBaseAddress
    )
    UnmapViewOfFile.restype = wintypes.BOOL

    GetFileSizeEx = windll.kernel32.GetFileSizeEx
    GetFileSizeEx.argtypes = (
        wintypes.HANDLE,  # hFile
        wintypes.PLARGE_INTEGER,  # lpFileSize
    )

    CheckSumMappedFile = windll.imagehlp.CheckSumMappedFile
    CheckSumMappedFile.argtypes = (
        wintypes.LPVOID,  # BaseAddress
        wintypes.DWORD,  # FileLength
        wintypes.PDWORD,  # HeaderSum
        wintypes.PDWORD,  # CheckSum
    )
    CheckSumMappedFile.restype = wintypes.LPVOID

    # 011348.python.winutils.line190.comment Open file
    hFile = CreateFileW(
        ctypes.c_wchar_p(exe_path),
        0x80000000,  # dwDesiredAccess = GENERIC_READ
        0x00000001 | 0x00000002,  # dwShareMode = FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,  # lpSecurityAttributes = NULL
        3,  # dwCreationDisposition = OPEN_EXISTING
        0x80,  # dwFlagsAndAttributes = FILE_ATTRIBUTE_NORMAL
        None  # hTemplateFile = NULL
    )
    if hFile == INVALID_HANDLE:
        err = GetLastError()
        raise RuntimeError(f"Failed to open file {exe_path}! Error code: {err}")

    # 011355.python.winutils.line204.comment Query file size
    fileLength = wintypes.LARGE_INTEGER(0)
    if GetFileSizeEx(hFile, fileLength) == 0:
        err = GetLastError()
        CloseHandle(hFile)
        raise RuntimeError(f"Failed to query file size file! Error code: {err}")
    fileLength = fileLength.value
    if fileLength > (2**32 - 1):
        raise RuntimeError("Executable size exceeds maximum allowed executable size on Windows (4 GiB)!")

    # 011356.python.winutils.line214.comment Map the file
    hMapping = CreateFileMappingW(
        hFile,
        None,  # lpFileMappingAttributes = NULL
        0x02,  # flProtect = PAGE_READONLY
        0,  # dwMaximumSizeHigh = 0
        0,  # dwMaximumSizeLow = 0
        None  # lpName = NULL
    )
    if not hMapping:
        err = GetLastError()
        CloseHandle(hFile)
        raise RuntimeError(f"Failed to map file! Error code: {err}")

    # 011362.python.winutils.line228.comment Create map view
    baseAddress = MapViewOfFile(
        hMapping,
        4,  # dwDesiredAccess = FILE_MAP_READ
        0,  # dwFileOffsetHigh = 0
        0,  # dwFileOffsetLow = 0
        0  # dwNumberOfBytesToMap = 0
    )
    if baseAddress == 0:
        err = GetLastError()
        CloseHandle(hMapping)
        CloseHandle(hFile)
        raise RuntimeError(f"Failed to create map view! Error code: {err}")

    # 011367.python.winutils.line242.comment Finally, compute the checksum
    headerSum = wintypes.DWORD(0)
    checkSum = wintypes.DWORD(0)
    ret = CheckSumMappedFile(baseAddress, fileLength, ctypes.byref(headerSum), ctypes.byref(checkSum))
    if ret is None:
        err = GetLastError()

    # 011368.python.winutils.line249.comment Cleanup
    UnmapViewOfFile(baseAddress)
    CloseHandle(hMapping)
    CloseHandle(hFile)

    if ret is None:
        raise RuntimeError(f"CheckSumMappedFile failed! Error code: {err}")

    return checkSum.value
