import os

import pythoncom
import pywintypes
import win32api
import win32com
import win32com.client
import win32com.client.dynamic
import win32com.server.util
import win32timezone
import win32ui
from win32com import storagecon
from win32com.axcontrol import axcontrol
from win32com.test.util import CheckClean

S_OK = 0

now = win32timezone.now()


class LockBytes:
    _public_methods_ = [
        "ReadAt",
        "WriteAt",
        "Flush",
        "SetSize",
        "LockRegion",
        "UnlockRegion",
        "Stat",
    ]
    _com_interfaces_ = [pythoncom.IID_ILockBytes]

    def __init__(self, data=b""):
        self.data = data
        self.ctime = now
        self.mtime = now
        self.atime = now

    def ReadAt(self, offset, cb):
        print("ReadAt")
        result = self.data[offset : offset + cb]
        return result

    def WriteAt(self, offset, data):
        print("WriteAt", offset)
        print("len", len(data))
        print("data:")
        # 050156.python.testPersist.line48.comment print(data)
        if len(self.data) >= offset:
            newdata = self.data[0:offset] + data
        print(len(newdata))
        if len(self.data) >= offset + len(data):
            newdata += self.data[offset + len(data) :]
        print(len(newdata))
        self.data = newdata
        return len(data)

    def Flush(self, whatsthis=0):
        print("Flush", whatsthis)
        fname = os.path.join(win32api.GetTempPath(), "persist.doc")
        open(fname, "wb").write(self.data)
        return S_OK

    def SetSize(self, size):
        print("Set Size", size)
        if size > len(self.data):
            self.data += b"\000" * (size - len(self.data))
        else:
            self.data = self.data[0:size]
        return S_OK

    def LockRegion(self, offset, size, locktype):
        print("LockRegion")

    def UnlockRegion(self, offset, size, locktype):
        print("UnlockRegion")

    def Stat(self, statflag):
        print("returning Stat", statflag)
        return (
            "PyMemBytes",
            storagecon.STGTY_LOCKBYTES,
            len(self.data),
            self.mtime,
            self.ctime,
            self.atime,
            storagecon.STGM_DIRECT | storagecon.STGM_READWRITE | storagecon.STGM_CREATE,
            storagecon.STGM_SHARE_EXCLUSIVE,
            "{00020905-0000-0000-C000-000000000046}",
            0,  # statebits ?
            0,
        )


class OleClientSite:
    _public_methods_ = [
        "SaveObject",
        "GetMoniker",
        "GetContainer",
        "ShowObject",
        "OnShowWindow",
        "RequestNewObjectLayout",
    ]
    _com_interfaces_ = [axcontrol.IID_IOleClientSite]

    def __init__(self, data=""):
        self.IPersistStorage = None
        self.IStorage = None

    def SetIPersistStorage(self, IPersistStorage):
        self.IPersistStorage = IPersistStorage

    def SetIStorage(self, IStorage):
        self.IStorage = IStorage

    def SaveObject(self):
        print("SaveObject")
        if self.IPersistStorage is not None and self.IStorage is not None:
            self.IPersistStorage.Save(self.IStorage, 1)
            self.IStorage.Commit(0)
        return S_OK

    def GetMoniker(self, dwAssign, dwWhichMoniker):
        print("GetMoniker", dwAssign, dwWhichMoniker)

    def GetContainer(self):
        print("GetContainer")

    def ShowObject(self):
        print("ShowObject")

    def OnShowWindow(self, fShow):
        print("ShowObject", fShow)

    def RequestNewObjectLayout(self):
        print("RequestNewObjectLayout")


def test():
    # 050158.python.testPersist.line140.comment create a LockBytes object and
    # 050159.python.testPersist.line141.comment wrap it as a COM object
    # 050160.python.testPersist.line142.comment import win32com.server.dispatcher
    lbcom = win32com.server.util.wrap(
        LockBytes(), pythoncom.IID_ILockBytes
    )  # , useDispatcher=win32com.server.dispatcher.DispatcherWin32trace)

    # 050162.python.testPersist.line147.comment create a structured storage on the ILockBytes object
    stcom = pythoncom.StgCreateDocfileOnILockBytes(
        lbcom,
        storagecon.STGM_DIRECT
        | storagecon.STGM_CREATE
        | storagecon.STGM_READWRITE
        | storagecon.STGM_SHARE_EXCLUSIVE,
        0,
    )

    # 050163.python.testPersist.line157.comment create our ClientSite
    ocs = OleClientSite()
    # 050164.python.testPersist.line159.comment wrap it as a COM object
    ocscom = win32com.server.util.wrap(ocs, axcontrol.IID_IOleClientSite)

    # 050165.python.testPersist.line162.comment create a Word OLE Document, connect it to our site and our storage
    oocom = axcontrol.OleCreate(
        "{00020906-0000-0000-C000-000000000046}",
        axcontrol.IID_IOleObject,
        0,
        (0,),
        ocscom,
        stcom,
    )

    mf = win32ui.GetMainFrame()
    hwnd = mf.GetSafeHwnd()

    # 050166.python.testPersist.line175.comment Set the host and document name
    # 050167.python.testPersist.line176.comment for unknown reason document name becomes hostname, and document name
    # 050168.python.testPersist.line177.comment is not set, debugged it, but don't know where the problem is?
    oocom.SetHostNames("OTPython", "This is Cool")

    # 050169.python.testPersist.line180.comment activate the OLE document
    oocom.DoVerb(-1, ocscom, 0, hwnd, mf.GetWindowRect())

    # 050170.python.testPersist.line183.comment set the hostnames again
    oocom.SetHostNames("OTPython2", "ThisisCool2")

    # 050171.python.testPersist.line186.comment get IDispatch of Word
    doc = win32com.client.Dispatch(oocom.QueryInterface(pythoncom.IID_IDispatch))

    # 050172.python.testPersist.line189.comment get IPersistStorage of Word
    dpcom = oocom.QueryInterface(pythoncom.IID_IPersistStorage)

    # 050173.python.testPersist.line192.comment let our ClientSite know the interfaces
    ocs.SetIPersistStorage(dpcom)
    ocs.SetIStorage(stcom)

    # 050174.python.testPersist.line196.comment use IDispatch to do the Office Word test
    # 050175.python.testPersist.line197.comment pasted from TestOffice.py

    wrange = doc.Range()
    for i in range(10):
        wrange.InsertAfter("Hello from Python %d\n" % i)
    paras = doc.Paragraphs
    for i in range(len(paras)):
        paras[i]().Font.ColorIndex = i + 1
        paras[i]().Font.Size = 12 + (4 * i)
    # 050176.python.testPersist.line206.comment XXX - note that
    # 050177.python.testPersist.line207.comment for para in paras:
    # 050178.python.testPersist.line208.comment para().Font...
    # 050179.python.testPersist.line209.comment doesn't seem to work - no error, just doesn't work
    # 050180.python.testPersist.line210.comment Should check if it works for VB!

    dpcom.Save(stcom, 0)
    dpcom.HandsOffStorage()
    # 050181.python.testPersist.line214.comment oocom.Close(axcontrol.OLECLOSE_NOSAVE) # or OLECLOSE_SAVEIFDIRTY, but it fails???

    # 050182.python.testPersist.line216.comment Save the ILockBytes data to "persist2.doc"
    lbcom.Flush()

    # 050183.python.testPersist.line219.comment exiting Winword will automatically update the ILockBytes data
    # 050184.python.testPersist.line220.comment and flush it to "%TEMP%\persist.doc"
    doc.Application.Quit()


if __name__ == "__main__":
    test()
    pythoncom.CoUninitialize()
    CheckClean()
