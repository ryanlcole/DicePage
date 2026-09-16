# 051787.python.icon_handler.line1.comment A sample icon handler.  Sets the icon for Python files to a random
# 051788.python.icon_handler.line2.comment ICO file.  ICO files are found in the Python directory - generally there will
# 051789.python.icon_handler.line3.comment be 3 icons found.
# 051790.python.icon_handler.line4.comment
# 051791.python.icon_handler.line5.comment To demonstrate:
# 051792.python.icon_handler.line6.comment * Execute this script to register the context menu.
# 051793.python.icon_handler.line7.comment * Open Windows Explorer, and browse to a directory with a .py file.
# 051794.python.icon_handler.line8.comment * Note the pretty, random selection of icons!
# 051795.python.icon_handler.line9.comment Use glob to locate ico files, and random.choice to pick one.
import glob
import os
import random
import sys

import pythoncom
import winerror
from win32com.shell import shell

ico_files = glob.glob(os.path.join(sys.prefix, "*.ico"))
if not ico_files:
    ico_files = glob.glob(os.path.join(sys.prefix, "PC", "*.ico"))
if not ico_files:
    print("WARNING: Can't find any icon files")

# 051796.python.icon_handler.line25.comment Our shell extension.
IExtractIcon_Methods = "Extract GetIconLocation".split()
IPersistFile_Methods = "IsDirty Load Save SaveCompleted GetCurFile".split()


class ShellExtension:
    _reg_progid_ = "Python.ShellExtension.IconHandler"
    _reg_desc_ = "Python Sample Shell Extension (icon handler)"
    _reg_clsid_ = "{a97e32d7-3b78-448c-b341-418120ea9227}"
    _com_interfaces_ = [shell.IID_IExtractIcon, pythoncom.IID_IPersistFile]
    _public_methods_ = IExtractIcon_Methods + IPersistFile_Methods

    def Load(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def GetIconLocation(self, flags):
        # 051797.python.icon_handler.line42.comment note - returning a single int will set the HRESULT (eg, S_FALSE,
        # 051798.python.icon_handler.line43.comment E_PENDING - see MS docs for details.
        return random.choice(ico_files), 0, 0

    def Extract(self, fname, index, size):
        return winerror.S_FALSE


def DllRegisterServer():
    import winreg

    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "Python.File\\shellex")
    subkey = winreg.CreateKey(key, "IconHandler")
    winreg.SetValueEx(subkey, None, 0, winreg.REG_SZ, ShellExtension._reg_clsid_)
    print(ShellExtension._reg_desc_, "registration complete.")


def DllUnregisterServer():
    import winreg

    try:
        key = winreg.DeleteKey(
            winreg.HKEY_CLASSES_ROOT, "Python.File\\shellex\\IconHandler"
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
