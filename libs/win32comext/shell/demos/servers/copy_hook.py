# 051608.python.copy_hook.line1.comment A sample shell copy hook.

# 051609.python.copy_hook.line3.comment To demonstrate:
# 051610.python.copy_hook.line4.comment * Execute this script to register the context menu.
# 051611.python.copy_hook.line5.comment * Open Windows Explorer
# 051612.python.copy_hook.line6.comment * Attempt to move or copy a directory.
# 051613.python.copy_hook.line7.comment * Note our hook's dialog is displayed.

import pythoncom
import win32con
import win32gui
from win32com.shell import shell


# 051614.python.copy_hook.line15.comment Our shell extension.
class ShellExtension:
    _reg_progid_ = "Python.ShellExtension.CopyHook"
    _reg_desc_ = "Python Sample Shell Extension (copy hook)"
    _reg_clsid_ = "{1845b6ba-2bbd-4197-b930-46d8651497c1}"
    _com_interfaces_ = [shell.IID_ICopyHook]
    _public_methods_ = ["CopyCallBack"]

    def CopyCallBack(self, hwnd, func, flags, srcName, srcAttr, destName, destAttr):
        # 051615.python.copy_hook.line24.comment This function should return:
        # 051616.python.copy_hook.line25.comment IDYES Allows the operation.
        # 051617.python.copy_hook.line26.comment IDNO Prevents the operation on this folder but continues with any other operations that have been approved (for example, a batch copy operation).
        # 051618.python.copy_hook.line27.comment IDCANCEL Prevents the current operation and cancels any pending operations.
        print("CopyCallBack", hwnd, func, flags, srcName, srcAttr, destName, destAttr)
        return win32gui.MessageBox(
            hwnd, "Allow operation?", "CopyHook", win32con.MB_YESNO
        )


def DllRegisterServer():
    import winreg

    key = winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        "directory\\shellex\\CopyHookHandlers\\" + ShellExtension._reg_desc_,
    )
    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, ShellExtension._reg_clsid_)
    key = winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        "*\\shellex\\CopyHookHandlers\\" + ShellExtension._reg_desc_,
    )
    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, ShellExtension._reg_clsid_)
    print(ShellExtension._reg_desc_, "registration complete.")


def DllUnregisterServer():
    import winreg

    try:
        key = winreg.DeleteKey(
            winreg.HKEY_CLASSES_ROOT,
            "directory\\shellex\\CopyHookHandlers\\" + ShellExtension._reg_desc_,
        )
    except OSError as details:
        import errno

        if details.errno != errno.ENOENT:
            raise
    try:
        key = winreg.DeleteKey(
            winreg.HKEY_CLASSES_ROOT,
            "*\\shellex\\CopyHookHandlers\\" + ShellExtension._reg_desc_,
        )
    except OSError as details:
        import errno

        if details.errno != errno.ENOENT:
            raise
    print(ShellExtension._reg_desc_, "unregistration complete.")


if __name__ == "__main__":
    from win32com.server import register

    register.UseCommandLine(
        ShellExtension,
        finalize_register=DllRegisterServer,
        finalize_unregister=DllUnregisterServer,
    )
# 051619.python.copy_hook.line84.comment !/usr/bin/env python
