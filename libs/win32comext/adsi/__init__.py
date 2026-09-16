import win32com
import win32com.client

if isinstance(__path__, str):
    # 050558.python.init.line5.comment For freeze to work!
    import sys

    try:
        import adsi

        sys.modules["win32com.adsi.adsi"] = adsi
    except ImportError:
        pass
else:
    # 050559.python.init.line15.comment See if we have a special directory for the binaries (for developers)
    win32com.__PackageSupportBuildPath__(__path__)


# 050560.python.init.line19.comment Some helpers
# 050561.python.init.line20.comment We want to _look_ like the ADSI module, but provide some additional
# 050562.python.init.line21.comment helpers.

# 050563.python.init.line23.comment Of specific note - most of the interfaces supported by ADSI
# 050564.python.init.line24.comment derive from IDispatch - thus, you get the custom methods from the
# 050565.python.init.line25.comment interface, as well as via IDispatch.
import pythoncom

from .adsi import *  # nopycln: import # Re-export everything from win32comext/adsi/adsi.pyd

LCID = 0

IDispatchType = pythoncom.TypeIIDs[pythoncom.IID_IDispatch]
IADsContainerType = pythoncom.TypeIIDs[adsi.IID_IADsContainer]


def _get_good_ret(
    ob,
    # 050567.python.init.line38.comment Named arguments used internally
    resultCLSID=None,
):
    assert resultCLSID is None, "Now have type info for ADSI objects - fix me!"
    # 050568.python.init.line42.comment See if the object supports IDispatch
    if hasattr(ob, "Invoke"):
        import win32com.client.dynamic

        name = "Dispatch wrapper around %r" % ob
        return win32com.client.dynamic.Dispatch(ob, name, ADSIDispatch)
    return ob


class ADSIEnumerator:
    def __init__(self, ob):
        # 050569.python.init.line53.comment Query the object for the container interface.
        self._cont_ = ob.QueryInterface(adsi.IID_IADsContainer)
        self._oleobj_ = adsi.ADsBuildEnumerator(self._cont_)  # a PyIADsEnumVARIANT
        self.index = -1

    def __getitem__(self, index):
        return self.__GetIndex(index)

    def __call__(self, index):
        return self.__GetIndex(index)

    def __GetIndex(self, index):
        if not isinstance(index, int):
            raise TypeError("Only integer indexes are supported for enumerators")
        if index != self.index + 1:
            # 050571.python.init.line68.comment Index requested out of sequence.
            raise ValueError("You must index this object sequentially")
        self.index = index
        result = adsi.ADsEnumerateNext(self._oleobj_, 1)
        if len(result):
            return _get_good_ret(result[0])
        # 050572.python.init.line74.comment Failed - reset for next time around.
        self.index = -1
        self._oleobj_ = adsi.ADsBuildEnumerator(self._cont_)  # a PyIADsEnumVARIANT
        raise IndexError("list index out of range")


class ADSIDispatch(win32com.client.CDispatch):
    def _wrap_dispatch_(self, ob, userName=None, returnCLSID=None):
        if not userName:
            userName = "ADSI-object"
        olerepr = win32com.client.dynamic.MakeOleRepr(ob, None, None)
        return ADSIDispatch(ob, olerepr, userName)

    def _NewEnum(self):
        try:
            return ADSIEnumerator(self)
        except pythoncom.com_error:
            # 050574.python.init.line91.comment doesn't support it - let our base try!
            return win32com.client.CDispatch._NewEnum(self)

    def __getattr__(self, attr):
        try:
            return getattr(self._oleobj_, attr)
        except AttributeError:
            return win32com.client.CDispatch.__getattr__(self, attr)

    def QueryInterface(self, iid):
        ret = self._oleobj_.QueryInterface(iid)
        return _get_good_ret(ret)


# 050575.python.init.line105.comment We override the adsi.pyd methods to do the right thing.
def ADsGetObject(path, iid=pythoncom.IID_IDispatch):
    ret = adsi.ADsGetObject(path, iid)
    return _get_good_ret(ret)


def ADsOpenObject(path, username, password, reserved=0, iid=pythoncom.IID_IDispatch):
    ret = adsi.ADsOpenObject(path, username, password, reserved, iid)
    return _get_good_ret(ret)
