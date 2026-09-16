# 050011.python.testExchange.line1.comment TestExchange = Exchange Server Dump
# 050012.python.testExchange.line2.comment Note that this code uses "CDO", which is unlikely to get the best choice.
# 050013.python.testExchange.line3.comment You should use the Outlook object model, or
# 050014.python.testExchange.line4.comment the win32com.mapi examples for a low-level interface.

import os

import pythoncom
from win32com.client import gencache

ammodule = None  # was the generated module!


def GetDefaultProfileName():
    import win32api
    import win32con

    try:
        key = win32api.RegOpenKey(
            win32con.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows Messaging Subsystem\\Profiles",
        )
        try:
            return win32api.RegQueryValueEx(key, "DefaultProfile")[0]
        finally:
            key.Close()
    except win32api.error:
        return None


# 050016.python.testExchange.line31.comment
# 050017.python.testExchange.line32.comment Recursive dump of folders.
# 050018.python.testExchange.line33.comment
def DumpFolder(folder, indent=0):
    print(" " * indent, folder.Name)
    folders = folder.Folders
    folder = folders.GetFirst()
    while folder:
        DumpFolder(folder, indent + 1)
        folder = folders.GetNext()


def DumpFolders(session):
    try:
        infostores = session.InfoStores
    except AttributeError:
        # 050019.python.testExchange.line47.comment later outlook?
        store = session.DefaultStore
        folder = store.GetRootFolder()
        DumpFolder(folder)
        return

    print(infostores)
    print("There are %d infostores" % infostores.Count)
    for i in range(infostores.Count):
        infostore = infostores[i + 1]
        print("Infostore = ", infostore.Name)
        try:
            folder = infostore.RootFolder
        except pythoncom.com_error as details:
            hr, msg, exc, arg = details
            # 050020.python.testExchange.line62.comment -2147221219 == MAPI_E_FAILONEPROVIDER - a single provider temporarily not available.
            if exc and exc[-1] == -2147221219:
                print("This info store is currently not available")
                continue
        DumpFolder(folder)


# 050021.python.testExchange.line69.comment Build a dictionary of property tags, so I can reverse look-up
# 050022.python.testExchange.line70.comment
PropTagsById = {}
if ammodule:
    for name, val in ammodule.constants.__dict__.items():
        PropTagsById[val] = name


def TestAddress(session):
    # 050023.python.testExchange.line78.comment entry = session.GetAddressEntry("Skip")
    # 050024.python.testExchange.line79.comment print(entry)
    pass


def TestUser(session):
    ae = session.CurrentUser
    fields = getattr(ae, "Fields", [])
    print("User has %d fields" % len(fields))
    for f in range(len(fields)):
        field = fields[f + 1]
        id = PropTagsById.get(field.ID, field.ID)
        print(f"{field.Name}/{id}={field.Value}")


def test():
    oldcwd = os.getcwd()
    try:
        session = gencache.EnsureDispatch("MAPI.Session")
        try:
            session.Logon(GetDefaultProfileName())
        except pythoncom.com_error as details:
            print("Could not log on to MAPI:", details)
            return
    except pythoncom.error:
        # 050025.python.testExchange.line103.comment no mapi.session - let's try outlook
        app = gencache.EnsureDispatch("Outlook.Application")
        session = app.Session

    try:
        TestUser(session)
        TestAddress(session)
        DumpFolders(session)
    finally:
        session.Logoff()
        # 050026.python.testExchange.line113.comment It appears Exchange will change the cwd on us :(
        os.chdir(oldcwd)


if __name__ == "__main__":
    from .util import CheckClean

    test()
    CheckClean()
