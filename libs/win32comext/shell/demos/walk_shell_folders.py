# 051977.python.walk_shell_folders.line1.comment A little sample that walks from the desktop into child
# 051978.python.walk_shell_folders.line2.comment items.
from win32com.shell import shell, shellcon


def walk(folder, depth=2, indent=""):
    try:
        pidls = folder.EnumObjects(0, shellcon.SHCONTF_FOLDERS)
    except shell.error:
        # 051979.python.walk_shell_folders.line10.comment no items
        return
    for pidl in pidls:
        dn = folder.GetDisplayNameOf(pidl, shellcon.SHGDN_NORMAL)
        print(indent, dn)
        if depth:
            try:
                child = folder.BindToObject(pidl, None, shell.IID_IShellFolder)
            except shell.error:
                pass
            else:
                walk(child, depth - 1, indent + " ")


walk(shell.SHGetDesktopFolder())
