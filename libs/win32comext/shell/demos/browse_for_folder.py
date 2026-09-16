# 051513.python.browse_for_folder.line1.comment A couple of samples using SHBrowseForFolder

import os

import win32gui
from win32com.shell import shell, shellcon


# 051514.python.browse_for_folder.line9.comment A callback procedure - called by SHBrowseForFolder
def BrowseCallbackProc(hwnd, msg, lp, data):
    if msg == shellcon.BFFM_INITIALIZED:
        win32gui.SendMessage(hwnd, shellcon.BFFM_SETSELECTION, 1, data)
    elif msg == shellcon.BFFM_SELCHANGED:
        # 051515.python.browse_for_folder.line14.comment Set the status text of the
        # 051516.python.browse_for_folder.line15.comment For this message, 'lp' is the address of the PIDL.
        pidl = shell.AddressAsPIDL(lp)
        try:
            path = shell.SHGetPathFromIDList(pidl)
            win32gui.SendMessage(hwnd, shellcon.BFFM_SETSTATUSTEXT, 0, path)
        except shell.error:
            # 051517.python.browse_for_folder.line21.comment No path for this PIDL
            pass


if __name__ == "__main__":
    # 051518.python.browse_for_folder.line26.comment Demonstrate a dialog with the cwd selected as the default - this
    # 051519.python.browse_for_folder.line27.comment must be done via a callback function.
    flags = shellcon.BIF_STATUSTEXT
    shell.SHBrowseForFolder(
        0,  # parent HWND
        None,  # root PIDL.
        "Default of %s" % os.getcwd(),  # title
        flags,  # flags
        BrowseCallbackProc,  # callback function
        os.getcwd(),  # 'data' param for the callback
    )
    # 051526.python.browse_for_folder.line37.comment Browse from this directory down only.
    # 051527.python.browse_for_folder.line38.comment Get the PIDL for the cwd.
    desktop = shell.SHGetDesktopFolder()
    cb, pidl, extra = desktop.ParseDisplayName(0, None, os.getcwd())
    shell.SHBrowseForFolder(
        0,  # parent HWND
        pidl,  # root PIDL.
        "From %s down only" % os.getcwd(),  # title
    )
