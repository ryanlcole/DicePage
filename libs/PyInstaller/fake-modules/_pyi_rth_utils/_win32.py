# 002814.python.win32.line1.comment -----------------------------------------------------------------------------
# 002815.python.win32.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 002816.python.win32.line3.comment
# 002817.python.win32.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 002818.python.win32.line5.comment you may not use this file except in compliance with the License.
# 002819.python.win32.line6.comment
# 002820.python.win32.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002821.python.win32.line8.comment
# 002822.python.win32.line9.comment SPDX-License-Identifier: Apache-2.0
# 002823.python.win32.line10.comment -----------------------------------------------------------------------------

import ctypes
import ctypes.wintypes

# 002824.python.win32.line15.comment Constants from win32 headers
TOKEN_QUERY = 0x0008

TokenUser = 1  # from TOKEN_INFORMATION_CLASS enum
TokenAppContainerSid = 31  # from TOKEN_INFORMATION_CLASS enum

ERROR_INSUFFICIENT_BUFFER = 122

INVALID_HANDLE = -1

FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x00000100
FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000

SDDL_REVISION1 = 1

# 002827.python.win32.line30.comment Structures for ConvertSidToStringSidW
PSID = ctypes.wintypes.LPVOID


class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Sid", PSID),
        ("Attributes", ctypes.wintypes.DWORD),
    ]


class TOKEN_USER(ctypes.Structure):
    _fields_ = [
        ("User", SID_AND_ATTRIBUTES),
    ]


PTOKEN_USER = ctypes.POINTER(TOKEN_USER)


class TOKEN_APPCONTAINER_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TokenAppContainer", PSID),
    ]


PTOKEN_APPCONTAINER_INFORMATION = ctypes.POINTER(TOKEN_APPCONTAINER_INFORMATION)

# 002828.python.win32.line58.comment SECURITY_ATTRIBUTES structure for CreateDirectoryW
PSECURITY_DESCRIPTOR = ctypes.wintypes.LPVOID


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", ctypes.wintypes.DWORD),
        ("lpSecurityDescriptor", PSECURITY_DESCRIPTOR),
        ("bInheritHandle", ctypes.wintypes.BOOL),
    ]


# 002829.python.win32.line70.comment win32 API functions, bound via ctypes.
# 002830.python.win32.line71.comment NOTE: we do not use ctypes.windll.<dll_name> to avoid modifying its (global) function prototypes, which might affect
# 002831.python.win32.line72.comment user's code.
advapi32 = ctypes.WinDLL("advapi32")
kernel32 = ctypes.WinDLL("kernel32")

advapi32.ConvertSidToStringSidW.restype = ctypes.wintypes.BOOL
advapi32.ConvertSidToStringSidW.argtypes = (
    PSID,  # [in] PSID Sid
    ctypes.POINTER(ctypes.wintypes.LPWSTR),  # [out] LPWSTR *StringSid
)

advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = ctypes.wintypes.BOOL
advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (
    ctypes.wintypes.LPCWSTR,  # [in] LPCWSTR StringSecurityDescriptor
    ctypes.wintypes.DWORD,  # [in] DWORD StringSDRevision
    ctypes.POINTER(PSECURITY_DESCRIPTOR),  # [out] PSECURITY_DESCRIPTOR *SecurityDescriptor
    ctypes.wintypes.PULONG,  # [out] PULONG SecurityDescriptorSize
)

advapi32.GetTokenInformation.restype = ctypes.wintypes.BOOL
advapi32.GetTokenInformation.argtypes = (
    ctypes.wintypes.HANDLE,  # [in] HANDLE TokenHandle
    ctypes.c_int,  # [in] TOKEN_INFORMATION_CLASS TokenInformationClass
    ctypes.wintypes.LPVOID,  # [out, optional] LPVOID TokenInformation
    ctypes.wintypes.DWORD,  # [in] DWORD TokenInformationLength
    ctypes.wintypes.PDWORD,  # [out] PDWORD ReturnLength
)

kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
kernel32.CloseHandle.argtypes = (
    ctypes.wintypes.HANDLE,  # [in] HANDLE hObject
)

kernel32.CreateDirectoryW.restype = ctypes.wintypes.BOOL
kernel32.CreateDirectoryW.argtypes = (
    ctypes.wintypes.LPCWSTR,  # [in] LPCWSTR lpPathName
    ctypes.POINTER(SECURITY_ATTRIBUTES),  # [in, optional] LPSECURITY_ATTRIBUTES lpSecurityAttributes
)

kernel32.FormatMessageW.restype = ctypes.wintypes.DWORD
kernel32.FormatMessageW.argtypes = (
    ctypes.wintypes.DWORD,  # [in] DWORD dwFlags
    ctypes.wintypes.LPCVOID,  # [in, optional] LPCVOID lpSource
    ctypes.wintypes.DWORD,  # [in] DWORD dwMessageId
    ctypes.wintypes.DWORD,  # [in] DWORD dwLanguageId
    ctypes.wintypes.LPWSTR,  # [out] LPWSTR lpBuffer
    ctypes.wintypes.DWORD,  # [in] DWORD nSize
    ctypes.wintypes.LPVOID,  # [in, optional] va_list *Arguments
)

kernel32.GetCurrentProcess.restype = ctypes.wintypes.HANDLE
# 002853.python.win32.line122.comment kernel32.GetCurrentProcess has no arguments

kernel32.GetLastError.restype = ctypes.wintypes.DWORD
# 002854.python.win32.line125.comment kernel32.GetLastError has no arguments

kernel32.LocalFree.restype = ctypes.wintypes.BOOL
kernel32.LocalFree.argtypes = (
    ctypes.wintypes.HLOCAL,  # [in] _Frees_ptr_opt_ HLOCAL hMem
)

kernel32.OpenProcessToken.restype = ctypes.wintypes.BOOL
kernel32.OpenProcessToken.argtypes = (
    ctypes.wintypes.HANDLE,  # [in] HANDLE ProcessHandle
    ctypes.wintypes.DWORD,  # [in] DWORD DesiredAccess
    ctypes.wintypes.PHANDLE,  # [out] PHANDLE TokenHandle
)


def _win_error_to_message(error_code):
    """
    Convert win32 error code to message.
    """
    message_wstr = ctypes.wintypes.LPWSTR(None)
    ret = kernel32.FormatMessageW(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
        None,  # lpSource
        error_code,  # dwMessageId
        0x400,  # dwLanguageId = MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT)
        ctypes.cast(
            ctypes.byref(message_wstr),
            ctypes.wintypes.LPWSTR,
        ),  # pointer to LPWSTR due to FORMAT_MESSAGE_ALLOCATE_BUFFER; needs to be cast to LPWSTR
        64,  # due to FORMAT_MESSAGE_ALLOCATE_BUFFER, this is minimum number of characters to allocate
        None,
    )
    if ret == 0:
        return None

    message = message_wstr.value
    kernel32.LocalFree(message_wstr)

    # 002864.python.win32.line163.comment Strip trailing CR/LF.
    if message:
        message = message.strip()
    return message


def _get_process_sid(token_information_class):
    """
    Obtain the SID from the current process by the given token information class.

    Args:
      token_information_class: Token information class identifying the SID that we're
          interested in. Only TokenUser and TokenAppContainerSid are supported.

    Returns: SID (if it could be fetched) or None if not available or on error.
    """
    process_token = ctypes.wintypes.HANDLE(INVALID_HANDLE)

    try:
        # 002865.python.win32.line182.comment Get access token for the current process
        ret = kernel32.OpenProcessToken(
            kernel32.GetCurrentProcess(),
            TOKEN_QUERY,
            ctypes.pointer(process_token),
        )
        if ret == 0:
            error_code = kernel32.GetLastError()
            raise RuntimeError(f"Failed to open process token! Error code: 0x{error_code:X}")

        # 002866.python.win32.line192.comment Query buffer size for sid
        token_info_size = ctypes.wintypes.DWORD(0)

        ret = advapi32.GetTokenInformation(
            process_token,
            token_information_class,
            None,
            0,
            ctypes.byref(token_info_size),
        )

        # 002867.python.win32.line203.comment We expect this call to fail with ERROR_INSUFFICIENT_BUFFER
        if ret == 0:
            error_code = kernel32.GetLastError()
            if error_code != ERROR_INSUFFICIENT_BUFFER:
                raise RuntimeError(f"Failed to query token information buffer size! Error code: 0x{error_code:X}")
        else:
            raise RuntimeError("Unexpected return value from GetTokenInformation!")

        # 002868.python.win32.line211.comment Allocate buffer
        token_info = ctypes.create_string_buffer(token_info_size.value)
        ret = advapi32.GetTokenInformation(
            process_token,
            token_information_class,
            token_info,
            token_info_size,
            ctypes.byref(token_info_size),
        )
        if ret == 0:
            error_code = kernel32.GetLastError()
            raise RuntimeError(f"Failed to query token information! Error code: 0x{error_code:X}")

        # 002869.python.win32.line224.comment Convert SID to string
        # 002870.python.win32.line225.comment Technically, when UserToken is used, we need to pass user_info->User.Sid,
        # 002871.python.win32.line226.comment but as they are at the beginning of the buffer, just pass the buffer instead...
        sid_wstr = ctypes.wintypes.LPWSTR(None)

        if token_information_class == TokenUser:
            sid = ctypes.cast(token_info, PTOKEN_USER).contents.User.Sid
        elif token_information_class == TokenAppContainerSid:
            sid = ctypes.cast(token_info, PTOKEN_APPCONTAINER_INFORMATION).contents.TokenAppContainer
        else:
            raise ValueError(f"Unexpected token information class: {token_information_class}")

        ret = advapi32.ConvertSidToStringSidW(sid, ctypes.pointer(sid_wstr))
        if ret == 0:
            error_code = kernel32.GetLastError()
            raise RuntimeError(f"Failed to convert SID to string! Error code: 0x{error_code:X}")
        sid = sid_wstr.value
        kernel32.LocalFree(sid_wstr)
    except Exception:
        sid = None
    finally:
        # 002872.python.win32.line245.comment Close the process token
        if process_token.value != INVALID_HANDLE:
            kernel32.CloseHandle(process_token)

    return sid


# 002873.python.win32.line252.comment Get and cache current user's SID
_user_sid = _get_process_sid(TokenUser)

# 002874.python.win32.line255.comment Get and cache current app container's SID (if any)
_app_container_sid = _get_process_sid(TokenAppContainerSid)


def secure_mkdir(dir_name):
    """
    Replacement for mkdir that limits the access to created directory to current user.
    """

    # 002875.python.win32.line264.comment Create security descriptor
    # 002876.python.win32.line265.comment Prefer actual user SID over SID S-1-3-4 (current owner), because at the time of writing, Wine does not properly
    # 002877.python.win32.line266.comment support the latter.
    user_sid = _user_sid or "S-1-3-4"

    # 002878.python.win32.line269.comment DACL descriptor (D):
    # 002879.python.win32.line270.comment ace_type;ace_flags;rights;object_guid;inherit_object_guid;account_sid;(resource_attribute)
    # 002880.python.win32.line271.comment - ace_type = SDDL_ACCESS_ALLOWED (A)
    # 002881.python.win32.line272.comment - rights = SDDL_FILE_ALL (FA)
    # 002882.python.win32.line273.comment - account_sid = current user (queried SID)
    security_desc_str = f"D:(A;;FA;;;{user_sid})"

    # 002883.python.win32.line276.comment If the app is running within an AppContainer, the app container SID has to be added to the DACL.
    # 002884.python.win32.line277.comment Otherwise our process will not have access to the temp dir.
    # 002885.python.win32.line278.comment
    # 002886.python.win32.line279.comment Quoting https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer:
    # 002887.python.win32.line280.comment "The AppContainer SID is a persistent unique identifier for the appcontainer. ...
    # 002888.python.win32.line281.comment To allow a single AppContainer to access a resource, add its AppContainerSID to the ACL for that resource."
    if _app_container_sid:
        security_desc_str += f"(A;;FA;;;{_app_container_sid})"
    security_desc = ctypes.wintypes.LPVOID(None)

    ret = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        security_desc_str,
        SDDL_REVISION1,
        ctypes.byref(security_desc),
        None,
    )
    if ret == 0:
        error_code = kernel32.GetLastError()
        raise RuntimeError(
            f"Failed to create security descriptor! Error code: 0x{error_code:X}, "
            f"message: {_win_error_to_message(error_code)}"
        )

    security_attr = SECURITY_ATTRIBUTES()
    security_attr.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
    security_attr.lpSecurityDescriptor = security_desc
    security_attr.bInheritHandle = False

    # 002889.python.win32.line304.comment Create directory
    ret = kernel32.CreateDirectoryW(
        dir_name,
        security_attr,
    )
    if ret == 0:
        # 002890.python.win32.line310.comment Call failed; store error code immediately, to avoid it being overwritten in cleanup below.
        error_code = kernel32.GetLastError()

    # 002891.python.win32.line313.comment Free security descriptor
    kernel32.LocalFree(security_desc)

    # 002892.python.win32.line316.comment Exit on succeess
    if ret != 0:
        return

    # 002893.python.win32.line320.comment Construct OSError from win error code
    error_message = _win_error_to_message(error_code)

    # 002894.python.win32.line323.comment Strip trailing dot to match error message from os.mkdir().
    if error_message and error_message[-1] == '.':
        error_message = error_message[:-1]

    raise OSError(
        None,  # errno
        error_message,  # strerror
        dir_name,  # filename
        error_code,  # winerror
        None,  # filename2
    )
