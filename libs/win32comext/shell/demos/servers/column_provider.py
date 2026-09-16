# 051568.python.column_provider.line1.comment A sample shell column provider
# 051569.python.column_provider.line2.comment Mainly ported from MSDN article:
# 051570.python.column_provider.line3.comment Using Shell Column Handlers for Detailed File Information,
# 051571.python.column_provider.line4.comment Raymond Chen, Microsoft Corporation, February 2000
# 051572.python.column_provider.line5.comment
# 051573.python.column_provider.line6.comment To demonstrate:
# 051574.python.column_provider.line7.comment * Execute this script to register the namespace.
# 051575.python.column_provider.line8.comment * Open Windows Explorer
# 051576.python.column_provider.line9.comment * Right-click an explorer column header - select "More"
# 051577.python.column_provider.line10.comment * Locate column 'pyc size' or 'pyo size', and add it to the view.
# 051578.python.column_provider.line11.comment This handler is providing that column data.
import os
import stat

import commctrl
import pythoncom
from pywintypes import IID
from win32com.shell import shell, shellcon

IPersist_Methods = ["GetClassID"]
IColumnProvider_Methods = IPersist_Methods + [
    "Initialize",
    "GetColumnInfo",
    "GetItemData",
]


class ColumnProvider:
    _reg_progid_ = "Python.ShellExtension.ColumnProvider"
    _reg_desc_ = "Python Sample Shell Extension (Column Provider)"
    _reg_clsid_ = IID("{0F14101A-E05E-4070-BD54-83DFA58C3D68}")
    _com_interfaces_ = [
        pythoncom.IID_IPersist,
        shell.IID_IColumnProvider,
    ]
    _public_methods_ = IColumnProvider_Methods

    # 051579.python.column_provider.line38.comment IPersist
    def GetClassID(self):
        return self._reg_clsid_

    # 051580.python.column_provider.line42.comment IColumnProvider
    def Initialize(self, colInit):
        flags, reserved, name = colInit
        print("ColumnProvider initializing for file", name)

    def GetColumnInfo(self, index):
        # 051581.python.column_provider.line48.comment We support exactly 2 columns - 'pyc size' and 'pyo size'
        if index in [0, 1]:
            # 051582.python.column_provider.line50.comment As per the MSDN sample, use our CLSID as the fmtid
            if index == 0:
                ext = ".pyc"
            else:
                ext = ".pyo"
            title = ext + " size"
            description = "Size of compiled %s file" % ext
            col_id = (self._reg_clsid_, index)  # fmtid  # pid
            col_info = (
                col_id,  # scid
                pythoncom.VT_I4,  # vt
                commctrl.LVCFMT_RIGHT,  # fmt
                20,  # cChars
                shellcon.SHCOLSTATE_TYPE_INT
                | shellcon.SHCOLSTATE_SECONDARYUI,  # csFlags
                title,
                description,
            )
            return col_info
        return None  # Indicate no more columns.

    def GetItemData(self, colid, colData):
        fmt_id, pid = colid
        fmt_id == self._reg_clsid_
        flags, attr, reserved, ext, name = colData
        if ext.lower() not in [".py", ".pyw"]:
            return None
        if pid == 0:
            ext = ".pyc"
        else:
            ext = ".pyo"
        check_file = os.path.splitext(name)[0] + ext
        try:
            st = os.stat(check_file)
            return st[stat.ST_SIZE]
        except OSError:
            # 051590.python.column_provider.line86.comment No file
            return None


def DllRegisterServer():
    import winreg

    # 051591.python.column_provider.line93.comment Special ColumnProvider key
    key = winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        "Folder\\ShellEx\\ColumnHandlers\\" + str(ColumnProvider._reg_clsid_),
    )
    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, ColumnProvider._reg_desc_)
    print(ColumnProvider._reg_desc_, "registration complete.")


def DllUnregisterServer():
    import winreg

    try:
        key = winreg.DeleteKey(
            winreg.HKEY_CLASSES_ROOT,
            "Folder\\ShellEx\\ColumnHandlers\\" + str(ColumnProvider._reg_clsid_),
        )
    except OSError as details:
        import errno

        if details.errno != errno.ENOENT:
            raise
    print(ColumnProvider._reg_desc_, "unregistration complete.")


if __name__ == "__main__":
    from win32com.server import register

    register.UseCommandLine(
        ColumnProvider,
        finalize_register=DllRegisterServer,
        finalize_unregister=DllUnregisterServer,
    )
