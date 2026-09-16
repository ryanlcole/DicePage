"""AXScript Client Framework

This module provides a core framework for an ActiveX Scripting client.
Derived classes actually implement the AX Client itself, including the
scoping rules, etc.

There are classes defined for the engine itself, and for ScriptItems
"""

from __future__ import annotations

import re
import sys
from typing import NoReturn

import pythoncom  # Need simple connection point support
import win32api
import win32com.client.connect
import win32com.server.util
import winerror
from win32com.axscript import axscript
from win32com.server.exception import COMException, IsCOMServerException

from . import error  # axscript.client.error


def RemoveCR(text):
    # 051022.python.framework.line28.comment No longer just "RemoveCR" - should be renamed to
    # 051023.python.framework.line29.comment FixNewlines, or something.  Idea is to fix arbitary newlines into
    # 051024.python.framework.line30.comment something Python can compile...
    return re.sub(r"(\r\n)|\r|(\n\r)", "\n", text)


SCRIPTTEXT_FORCEEXECUTION = -2147483648  # 0x80000000
SCRIPTTEXT_ISEXPRESSION = 0x00000020
SCRIPTTEXT_ISPERSISTENT = 0x00000040


state_map = {
    axscript.SCRIPTSTATE_UNINITIALIZED: "SCRIPTSTATE_UNINITIALIZED",
    axscript.SCRIPTSTATE_INITIALIZED: "SCRIPTSTATE_INITIALIZED",
    axscript.SCRIPTSTATE_STARTED: "SCRIPTSTATE_STARTED",
    axscript.SCRIPTSTATE_CONNECTED: "SCRIPTSTATE_CONNECTED",
    axscript.SCRIPTSTATE_DISCONNECTED: "SCRIPTSTATE_DISCONNECTED",
    axscript.SCRIPTSTATE_CLOSED: "SCRIPTSTATE_CLOSED",
}


def profile(fn, *args):
    import profile

    prof = profile.Profile()
    try:
        # 051026.python.framework.line54.comment roll on 1.6 :-)
        # 051027.python.framework.line55.comment return prof.runcall(fn, *args)
        return prof.runcall(*(fn,) + args)
    finally:
        import pstats

        # 051028.python.framework.line60.comment Damn - really want to send this to Excel!
        # 051029.python.framework.line61.comment width, list = pstats.Stats(prof).strip_dirs().get_print_list([])
        pstats.Stats(prof).strip_dirs().sort_stats("time").print_stats()


class SafeOutput:
    softspace = 1

    def __init__(self, redir=None):
        if redir is None:
            redir = sys.stdout
        self.redir = redir

    def write(self, message):
        try:
            self.redir.write(message)
        except:
            win32api.OutputDebugString(message)

    def flush(self):
        pass

    def close(self):
        pass


# 051030.python.framework.line86.comment Make sure we have a valid sys.stdout/stderr, otherwise out
# 051031.python.framework.line87.comment print and trace statements may raise an exception
def MakeValidSysOuts():
    if not isinstance(sys.stdout, SafeOutput):
        sys.stdout = sys.stderr = SafeOutput()
        # 051032.python.framework.line91.comment and for the sake of working around something I can't understand...
        # 051033.python.framework.line92.comment prevent keyboard interrupts from killing IIS
        import signal

        def noOp(a, b):
            # 051034.python.framework.line96.comment it would be nice to get to the bottom of this, so a warning to
            # 051035.python.framework.line97.comment the debug console can't hurt.
            print("WARNING: Ignoring keyboard interrupt from ActiveScripting engine")

        # 051036.python.framework.line100.comment If someone else has already redirected, then assume they know what they are doing!
        if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
            try:
                signal.signal(signal.SIGINT, noOp)
            except ValueError:
                # 051037.python.framework.line105.comment Not the main thread - can't do much.
                pass


def trace(*args):
    """A function used instead of "print" for debugging output."""
    for arg in args:
        print(arg, end=" ")
    print()


def RaiseAssert(scode, desc) -> NoReturn:
    """A debugging function that raises an exception considered an "Assertion"."""
    print("**************** ASSERTION FAILED *******************")
    print(desc)
    raise COMException(desc, scode)


class AXScriptCodeBlock:
    """An object which represents a chunk of code in an AX Script"""

    def __init__(
        self,
        name: str,
        codeText: str,
        sourceContextCookie: int,
        startLineNumber: int,
        flags,
    ):
        self.name = name
        self.codeText = codeText
        self.codeObject = None
        self.sourceContextCookie = sourceContextCookie
        self.startLineNumber = startLineNumber
        self.flags = flags
        self.beenExecuted = 0

    def GetFileName(self):
        # 051038.python.framework.line143.comment Gets the "file name" for Python - uses <...> so Python doesn't think
        # 051039.python.framework.line144.comment it is a real file.
        return "<%s>" % self.name

    def GetDisplayName(self):
        return self.name

    def GetLineNo(self, no: int):
        pos = -1
        for i in range(no - 1):
            pos = self.codeText.find("\n", pos + 1)
            if pos == -1:
                pos = len(self.codeText)
        epos = self.codeText.find("\n", pos + 1)
        if epos == -1:
            epos = len(self.codeText)
        return self.codeText[pos + 1 : epos].strip()


class Event:
    """A single event for a ActiveX named object."""

    def __init__(self):
        self.name = "<None>"

    def __repr__(self):
        return "<%s at %d: %s>" % (self.__class__.__name__, id(self), self.name)

    def Reset(self):
        pass

    def Close(self):
        pass

    def Build(self, typeinfo, funcdesc):
        self.dispid = funcdesc[0]
        self.name = typeinfo.GetNames(self.dispid)[0]


# 051040.python.framework.line182.comment print("Event.Build() - Event Name is ", self.name)


class EventSink:
    """A set of events against an item.  Note this is a COM client for connection points."""

    _public_methods_: list[str] = []

    def __init__(self, myItem, coDispatch):
        self.events = {}
        self.connection = None
        self.coDispatch = coDispatch
        self.myScriptItem = myItem
        self.myInvokeMethod = myItem.GetEngine().ProcessScriptItemEvent
        self.iid = None

    def Reset(self):
        self.Disconnect()

    def Close(self):
        self.iid = None
        self.myScriptItem = None
        self.myInvokeMethod = None
        self.coDispatch = None
        for event in self.events.values():
            event.Reset()
        self.events = {}
        self.Disconnect()

    # 051041.python.framework.line211.comment COM Connection point methods.
    def _query_interface_(self, iid):
        if iid == self.iid:
            return win32com.server.util.wrap(self)

    def _invoke_(self, dispid, lcid, wFlags, args):
        try:
            event = self.events[dispid]
        except:
            raise COMException(scode=winerror.DISP_E_MEMBERNOTFOUND)
        # 051042.python.framework.line221.comment print("Invoke for ", event, "on", self.myScriptItem, " - calling",  self.myInvokeMethod)
        return self.myInvokeMethod(self.myScriptItem, event, lcid, wFlags, args)

    def GetSourceTypeInfo(self, typeinfo):
        """Gets the typeinfo for the Source Events for the passed typeinfo"""
        attr = typeinfo.GetTypeAttr()
        cFuncs = attr[6]
        typeKind = attr[5]
        if typeKind not in [pythoncom.TKIND_COCLASS, pythoncom.TKIND_INTERFACE]:
            RaiseAssert(
                winerror.E_UNEXPECTED, "The typeKind of the object is unexpected"
            )
        cImplType = attr[8]
        for i in range(cImplType):
            # 051043.python.framework.line235.comment Look for the [source, default] interface on the coclass
            # 051044.python.framework.line236.comment that isn't marked as restricted.
            flags = typeinfo.GetImplTypeFlags(i)
            flagsNeeded = (
                pythoncom.IMPLTYPEFLAG_FDEFAULT | pythoncom.IMPLTYPEFLAG_FSOURCE
            )
            if (flags & (flagsNeeded | pythoncom.IMPLTYPEFLAG_FRESTRICTED)) == (
                flagsNeeded
            ):
                # 051045.python.framework.line244.comment Get the handle to the implemented interface.
                href = typeinfo.GetRefTypeOfImplType(i)
                return typeinfo.GetRefTypeInfo(href)

    def BuildEvents(self):
        # 051046.python.framework.line249.comment See if it is an extender object.
        try:
            mainTypeInfo = self.coDispatch.QueryInterface(
                axscript.IID_IProvideMultipleClassInfo
            )
            isMulti = 1
            numTypeInfos = mainTypeInfo.GetMultiTypeInfoCount()
        except pythoncom.com_error:
            isMulti = 0
            numTypeInfos = 1
            try:
                mainTypeInfo = self.coDispatch.QueryInterface(
                    pythoncom.IID_IProvideClassInfo
                )
            except pythoncom.com_error:
                numTypeInfos = 0
        # 051047.python.framework.line265.comment Create an event handler for the item.
        for item in range(numTypeInfos):
            if isMulti:
                typeinfo, flags = mainTypeInfo.GetInfoOfIndex(
                    item, axscript.MULTICLASSINFO_GETTYPEINFO
                )
            else:
                typeinfo = mainTypeInfo.GetClassInfo()
            sourceType = self.GetSourceTypeInfo(typeinfo)
            cFuncs = 0
            if sourceType:
                attr = sourceType.GetTypeAttr()
                self.iid = attr[0]
                cFuncs = attr[6]
                for i in range(cFuncs):
                    funcdesc = sourceType.GetFuncDesc(i)
                    event = Event()
                    event.Build(sourceType, funcdesc)
                    self.events[event.dispid] = event

    def Connect(self):
        if self.connection is not None or self.iid is None:
            return
        # 051048.python.framework.line288.comment trace("Connect for sink item", self.myScriptItem.name, "with IID",str(self.iid))
        self.connection = win32com.client.connect.SimpleConnection(
            self.coDispatch, self, self.iid
        )

    def Disconnect(self):
        if self.connection:
            try:
                self.connection.Disconnect()
            except pythoncom.com_error:
                pass  # Ignore disconnection errors.
            self.connection = None


class ScriptItem:
    """An item (or subitem) that is exposed to the ActiveX script"""

    def __init__(self, parentItem, name, dispatch, flags):
        self.parentItem = parentItem
        self.dispatch = dispatch
        self.name = name
        self.flags = flags
        self.eventSink = None
        self.subItems = {}
        self.createdConnections = 0
        self.isRegistered = 0

    # 051050.python.framework.line315.comment trace("Creating ScriptItem", name, "of parent", parentItem,"with dispatch", dispatch)

    def __repr__(self):
        flagsDesc = ""
        if self.flags is not None and self.flags & axscript.SCRIPTITEM_GLOBALMEMBERS:
            flagsDesc = "/Global"
        return "<%s at %d: %s%s>" % (
            self.__class__.__name__,
            id(self),
            self.name,
            flagsDesc,
        )

    def _dump_(self, level):
        flagDescs = []
        if self.flags is not None and self.flags & axscript.SCRIPTITEM_GLOBALMEMBERS:
            flagDescs.append("GLOBAL!")
        if self.flags is None or self.flags & axscript.SCRIPTITEM_ISVISIBLE == 0:
            flagDescs.append("NOT VISIBLE")
        if self.flags is not None and self.flags & axscript.SCRIPTITEM_ISSOURCE:
            flagDescs.append("EVENT SINK")
        if self.flags is not None and self.flags & axscript.SCRIPTITEM_CODEONLY:
            flagDescs.append("CODE ONLY")
        print(" " * level, "Name=", self.name, ", flags=", "/".join(flagDescs), self)
        for subItem in self.subItems.values():
            subItem._dump_(level + 1)

    def Reset(self):
        self.Disconnect()
        if self.eventSink:
            self.eventSink.Reset()
        self.isRegistered = 0
        for subItem in self.subItems.values():
            subItem.Reset()

    def Close(self):
        self.Reset()
        self.dispatch = None
        self.parentItem = None
        if self.eventSink:
            self.eventSink.Close()
            self.eventSink = None
        for subItem in self.subItems.values():
            subItem.Close()
        self.subItems = []
        self.createdConnections = 0

    def Register(self):
        if self.isRegistered:
            return
        # 051051.python.framework.line365.comment Get the type info to use to build this item.
        # 051052.python.framework.line366.comment if not self.dispatch:
        # 051053.python.framework.line367.comment id = self.parentItem.dispatch.GetIDsOfNames(self.name)
        # 051054.python.framework.line368.comment print("DispID of me is", id)
        # 051055.python.framework.line369.comment result = self.parentItem.dispatch.Invoke(id, 0, pythoncom.DISPATCH_PROPERTYGET,1)
        # 051056.python.framework.line370.comment if isinstance(result, pythoncom.TypeIIDs[pythoncom.IID_IDispatch]):
        # 051057.python.framework.line371.comment self.dispatch = result
        # 051058.python.framework.line372.comment else:
        # 051059.python.framework.line373.comment print("*** No dispatch")
        # 051060.python.framework.line374.comment return
        # 051061.python.framework.line375.comment print("**** Made dispatch")
        self.isRegistered = 1
        # 051062.python.framework.line377.comment Register the sub-items.
        for item in self.subItems.values():
            if not item.isRegistered:
                item.Register()

    def IsGlobal(self):
        return self.flags & axscript.SCRIPTITEM_GLOBALMEMBERS

    def IsVisible(self):
        return (
            self.flags & (axscript.SCRIPTITEM_ISVISIBLE | axscript.SCRIPTITEM_ISSOURCE)
        ) != 0

    def GetEngine(self):
        item = self
        while item.parentItem.__class__ == self.__class__:
            item = item.parentItem
        return item.parentItem

    def _GetFullItemName(self):
        ret = self.name
        if self.parentItem:
            try:
                ret = self.parentItem._GetFullItemName() + "." + ret
            except AttributeError:
                pass
        return ret

    def GetSubItemClass(self):
        return self.__class__

    def GetSubItem(self, name):
        return self.subItems[name.lower()]

    def GetCreateSubItem(self, parentItem, name, dispatch, flags):
        keyName = name.lower()
        try:
            rc = self.subItems[keyName]
            # 051063.python.framework.line415.comment No changes allowed to existing flags.
            if not rc.flags is None and not flags is None and rc.flags != flags:
                raise COMException(scode=winerror.E_INVALIDARG)
            # 051064.python.framework.line418.comment Existing item must not have a dispatch.
            if not rc.dispatch is None and not dispatch is None:
                raise COMException(scode=winerror.E_INVALIDARG)
            rc.flags = flags  # Setup the real flags.
            rc.dispatch = dispatch
        except KeyError:
            rc = self.subItems[keyName] = self.GetSubItemClass()(
                parentItem, name, dispatch, flags
            )
        return rc

    # 051066.python.framework.line429.comment if self.dispatch is None:
    # 051067.python.framework.line430.comment RaiseAssert(winerror.E_UNEXPECTED, "??")

    def CreateConnections(self):
        # 051068.python.framework.line433.comment Create (but do not connect to) the connection points.
        if self.createdConnections:
            return
        self.createdConnections = 1
        # 051069.python.framework.line437.comment Nothing to do unless this is an event source
        # 051070.python.framework.line438.comment This flags means self, _and_ children, are connectable.
        if self.flags & axscript.SCRIPTITEM_ISSOURCE:
            self.BuildEvents()
            self.FindBuildSubItemEvents()

    def Connect(self):
        # 051071.python.framework.line444.comment Connect to the already created connection points.
        if self.eventSink:
            self.eventSink.Connect()
        for subItem in self.subItems.values():
            subItem.Connect()

    def Disconnect(self):
        # 051072.python.framework.line451.comment Disconnect from the connection points.
        if self.eventSink:
            self.eventSink.Disconnect()
        for subItem in self.subItems.values():
            subItem.Disconnect()

    def BuildEvents(self):
        if self.eventSink is not None or self.dispatch is None:
            RaiseAssert(
                winerror.E_UNEXPECTED,
                "Item already has built events, or no dispatch available?",
            )

        # 051073.python.framework.line464.comment trace("BuildEvents for named item", self._GetFullItemName())
        self.eventSink = EventSink(self, self.dispatch)
        self.eventSink.BuildEvents()

    def FindBuildSubItemEvents(self):
        # 051074.python.framework.line469.comment Called during connection to event source.  Seeks out and connects to
        # 051075.python.framework.line470.comment all children.  As per the AX spec, this is not recursive
        # 051076.python.framework.line471.comment (ie, children sub-items are not seeked)
        try:
            multiTypeInfo = self.dispatch.QueryInterface(
                axscript.IID_IProvideMultipleClassInfo
            )
            numTypeInfos = multiTypeInfo.GetMultiTypeInfoCount()
        except pythoncom.com_error:
            return
        for item in range(numTypeInfos):
            typeinfo, flags = multiTypeInfo.GetInfoOfIndex(
                item, axscript.MULTICLASSINFO_GETTYPEINFO
            )
            defaultType = self.GetDefaultSourceTypeInfo(typeinfo)
            index = 0
            while 1:
                try:
                    fdesc = defaultType.GetFuncDesc(index)
                except pythoncom.com_error:
                    break  # No more funcs
                index += 1
                dispid = fdesc[0]
                funckind = fdesc[3]
                invkind = fdesc[4]
                elemdesc = fdesc[8]
                funcflags = fdesc[9]
                try:
                    isSubObject = (
                        not (funcflags & pythoncom.FUNCFLAG_FRESTRICTED)
                        and funckind == pythoncom.FUNC_DISPATCH
                        and invkind == pythoncom.INVOKE_PROPERTYGET
                        and elemdesc[0][0] == pythoncom.VT_PTR
                        and elemdesc[0][1][0] == pythoncom.VT_USERDEFINED
                    )
                except:
                    isSubObject = 0
                if isSubObject:
                    try:
                        # 051078.python.framework.line508.comment We found a sub-object.
                        names = typeinfo.GetNames(dispid)
                        result = self.dispatch.Invoke(
                            dispid, 0x0, pythoncom.DISPATCH_PROPERTYGET, 1
                        )
                        # 051079.python.framework.line513.comment IE has an interesting problem - there are lots of synonyms for the same object.  Eg
                        # 051080.python.framework.line514.comment in a simple form, "window.top", "window.window", "window.parent", "window.self"
                        # 051081.python.framework.line515.comment all refer to the same object.  Our event implementation code does not differentiate
                        # 051082.python.framework.line516.comment eg, "window_onload" will fire for *all* objects named "window".  Thus,
                        # 051083.python.framework.line517.comment "window" and "window.window" will fire the same event handler :(
                        # 051084.python.framework.line518.comment One option would be to check if the sub-object is indeed the
                        # 051085.python.framework.line519.comment parent object - however, this would stop "top_onload" from firing,
                        # 051086.python.framework.line520.comment as no event handler for "top" would work.
                        # 051087.python.framework.line521.comment I think we simply need to connect to a *single* event handler.
                        # 051088.python.framework.line522.comment As use in IE is deprecated, I am not solving this now.
                        if isinstance(
                            result, pythoncom.TypeIIDs[pythoncom.IID_IDispatch]
                        ):
                            name = names[0]
                            subObj = self.GetCreateSubItem(
                                self, name, result, axscript.SCRIPTITEM_ISVISIBLE
                            )
                            # 051089.python.framework.line530.comment print(
                            # 051090.python.framework.line531.comment "subobj",
                            # 051091.python.framework.line532.comment name,
                            # 051092.python.framework.line533.comment "flags are",
                            # 051093.python.framework.line534.comment subObj.flags,
                            # 051094.python.framework.line535.comment "mydisp=",
                            # 051095.python.framework.line536.comment self.dispatch,
                            # 051096.python.framework.line537.comment "result disp=",
                            # 051097.python.framework.line538.comment result,
                            # 051098.python.framework.line539.comment "compare=",
                            # 051099.python.framework.line540.comment self.dispatch == result,
                            # 051100.python.framework.line541.comment )
                            subObj.BuildEvents()
                            subObj.Register()
                    except pythoncom.com_error:
                        pass

    def GetDefaultSourceTypeInfo(self, typeinfo):
        """Gets the typeinfo for the Default Dispatch for the passed typeinfo"""
        attr = typeinfo.GetTypeAttr()
        cFuncs = attr[6]
        typeKind = attr[5]
        if typeKind not in [pythoncom.TKIND_COCLASS, pythoncom.TKIND_INTERFACE]:
            RaiseAssert(
                winerror.E_UNEXPECTED, "The typeKind of the object is unexpected"
            )
        cImplType = attr[8]
        for i in range(cImplType):
            # 051101.python.framework.line558.comment Look for the [source, default] interface on the coclass
            # 051102.python.framework.line559.comment that isn't marked as restricted.
            flags = typeinfo.GetImplTypeFlags(i)
            if (
                flags
                & (
                    pythoncom.IMPLTYPEFLAG_FDEFAULT
                    | pythoncom.IMPLTYPEFLAG_FSOURCE
                    | pythoncom.IMPLTYPEFLAG_FRESTRICTED
                )
            ) == pythoncom.IMPLTYPEFLAG_FDEFAULT:
                # 051103.python.framework.line569.comment Get the handle to the implemented interface.
                href = typeinfo.GetRefTypeOfImplType(i)
                defTypeInfo = typeinfo.GetRefTypeInfo(href)
                attr = defTypeInfo.GetTypeAttr()
                typeKind = attr[5]
                typeFlags = attr[11]
                if (
                    typeKind == pythoncom.TKIND_INTERFACE
                    and typeFlags & pythoncom.TYPEFLAG_FDUAL
                ):
                    # 051104.python.framework.line579.comment Get corresponding Disp interface
                    # 051105.python.framework.line580.comment -1 is a special value which does this for us.
                    href = typeinfo.GetRefTypeOfImplType(-1)
                    return defTypeInfo.GetRefTypeInfo(href)
                else:
                    return defTypeInfo


IActiveScriptMethods = [
    "SetScriptSite",
    "GetScriptSite",
    "SetScriptState",
    "GetScriptState",
    "Close",
    "AddNamedItem",
    "AddTypeLib",
    "GetScriptDispatch",
    "GetCurrentScriptThreadID",
    "GetScriptThreadID",
    "GetScriptThreadState",
    "InterruptScriptThread",
    "Clone",
]
IActiveScriptParseMethods = ["InitNew", "AddScriptlet", "ParseScriptText"]
IObjectSafetyMethods = ["GetInterfaceSafetyOptions", "SetInterfaceSafetyOptions"]

# 051106.python.framework.line605.comment ActiveScriptParseProcedure is a new interface with IIS4/IE4.
IActiveScriptParseProcedureMethods = ["ParseProcedureText"]


class COMScript:
    """An ActiveX Scripting engine base class.

    This class implements the required COM interfaces for ActiveX scripting.
    """

    _public_methods_ = (
        IActiveScriptMethods
        + IActiveScriptParseMethods
        + IObjectSafetyMethods
        + IActiveScriptParseProcedureMethods
    )
    _com_interfaces_ = [
        axscript.IID_IActiveScript,
        axscript.IID_IActiveScriptParse,
        axscript.IID_IObjectSafety,
    ]  # , axscript.IID_IActiveScriptParseProcedure]

    def __init__(self):
        # 051108.python.framework.line628.comment Make sure we can print/trace wihout an exception!
        MakeValidSysOuts()
        # 051109.python.framework.line630.comment trace("AXScriptEngine object created", self)
        self.baseThreadId = -1
        self.debugManager = None
        self.threadState = axscript.SCRIPTTHREADSTATE_NOTINSCRIPT
        self.scriptState = axscript.SCRIPTSTATE_UNINITIALIZED
        self.scriptSite = None
        self.safetyOptions = 0
        self.lcid = 0
        self.subItems = {}
        self.scriptCodeBlocks: dict[str, AXScriptCodeBlock] = {}

    def _query_interface_(self, iid):
        if self.debugManager:
            return self.debugManager._query_interface_for_debugger_(iid)
        # 051110.python.framework.line644.comment trace("ScriptEngine QI - unknown IID", iid)
        return 0

    # 051111.python.framework.line647.comment IActiveScriptParse
    def InitNew(self):
        if self.scriptSite is not None:
            self.SetScriptState(axscript.SCRIPTSTATE_INITIALIZED)

    def AddScriptlet(
        self,
        defaultName,
        code,
        itemName,
        subItemName,
        eventName,
        delimiter,
        sourceContextCookie,
        startLineNumber,
    ):
        # 051112.python.framework.line663.comment trace ("AddScriptlet", defaultName, code, itemName, subItemName, eventName, delimiter, sourceContextCookie, startLineNumber)
        self.DoAddScriptlet(
            defaultName,
            code,
            itemName,
            subItemName,
            eventName,
            delimiter,
            sourceContextCookie,
            startLineNumber,
        )

    def ParseScriptText(
        self,
        code,
        itemName,
        context,
        delimiter,
        sourceContextCookie,
        startLineNumber,
        flags,
        bWantResult,
    ):
        # 051113.python.framework.line686.comment trace ("ParseScriptText", code[:20],"...", itemName, context, delimiter, sourceContextCookie, startLineNumber, flags, bWantResult)
        if (
            bWantResult
            or self.scriptState == axscript.SCRIPTSTATE_STARTED
            or self.scriptState == axscript.SCRIPTSTATE_CONNECTED
            or self.scriptState == axscript.SCRIPTSTATE_DISCONNECTED
        ):
            flags |= SCRIPTTEXT_FORCEEXECUTION
        else:
            flags &= ~SCRIPTTEXT_FORCEEXECUTION

        if flags & SCRIPTTEXT_FORCEEXECUTION:
            # 051114.python.framework.line698.comment About to execute the code.
            self.RegisterNewNamedItems()
        return self.DoParseScriptText(
            code, sourceContextCookie, startLineNumber, bWantResult, flags
        )

    # 051115.python.framework.line704.comment
    # 051116.python.framework.line705.comment IActiveScriptParseProcedure
    def ParseProcedureText(
        self,
        code,
        formalParams,
        procName,
        itemName,
        unkContext,
        delimiter,
        contextCookie,
        startingLineNumber,
        flags,
    ):
        trace(
            "ParseProcedureText",
            code,
            formalParams,
            procName,
            itemName,
            unkContext,
            delimiter,
            contextCookie,
            startingLineNumber,
            flags,
        )
        # 051117.python.framework.line730.comment NOTE - this is never called, as we have disabled this interface.
        # 051118.python.framework.line731.comment Problem is, once enabled all even code comes via here, rather than AddScriptlet.
        # 051119.python.framework.line732.comment However, the "procName" is always an empty string - ie, itemName is the object whose event we are handling,
        # 051120.python.framework.line733.comment but no idea what the specific event is!?
        # 051121.python.framework.line734.comment Problem is disabling this block is that AddScriptlet is _not_ passed
        # 051122.python.framework.line735.comment <SCRIPT for="whatever" event="onClick" language="Python">
        # 051123.python.framework.line736.comment (but even for those blocks, the "onClick" information is still missing!?!?!?)

        # 051124.python.framework.line738.comment self.DoAddScriptlet(None, code, itemName, subItemName, eventName, delimiter,sourceContextCookie, startLineNumber)
        return None

    # 051125.python.framework.line741.comment
    # 051126.python.framework.line742.comment IActiveScript
    def SetScriptSite(self, site):
        # 051127.python.framework.line744.comment We should still work with an existing site (or so MSXML believes :)
        self.scriptSite = site
        if self.debugManager is not None:
            self.debugManager.Close()
        import traceback

        try:
            import win32com.axdebug.axdebug  # see if the core exists.

            from . import debug

            self.debugManager = debug.DebugManager(self)
        except pythoncom.com_error:
            # 051129.python.framework.line757.comment COM errors will occur if the debugger interface has never been
            # 051130.python.framework.line758.comment seen on the target system
            trace("Debugging interfaces not available - debugging is disabled..")
            self.debugManager = None
        except ImportError:
            trace(
                "Debugging extensions (axdebug) module does not exist - debugging is disabled.."
            )
            self.debugManager = None
        except:
            traceback.print_exc()
            trace(
                "*** Debugger Manager could not initialize - {}: {}".format(
                    sys.exc_info()[0], sys.exc_info()[1]
                )
            )
            self.debugManager = None

        try:
            self.lcid = site.GetLCID()
        except pythoncom.com_error:
            self.lcid = win32api.GetUserDefaultLCID()
        self.Reset()

    def GetScriptSite(self, iid):
        if self.scriptSite is None:
            raise COMException(scode=winerror.S_FALSE)
        return self.scriptSite.QueryInterface(iid)

    def SetScriptState(self, state):
        # 051131.python.framework.line787.comment print(f"SetScriptState with {state_map.get(state)} - currentstate = {state_map.get(self.scriptState)}"
        if state == self.scriptState:
            return
        # 051132.python.framework.line790.comment If closed, allow no other state transitions
        if self.scriptState == axscript.SCRIPTSTATE_CLOSED:
            raise COMException(scode=winerror.E_INVALIDARG)

        if state == axscript.SCRIPTSTATE_INITIALIZED:
            # 051133.python.framework.line795.comment Re-initialize - shutdown then reset.
            if self.scriptState in [
                axscript.SCRIPTSTATE_CONNECTED,
                axscript.SCRIPTSTATE_STARTED,
            ]:
                self.Stop()
        elif state == axscript.SCRIPTSTATE_STARTED:
            if self.scriptState == axscript.SCRIPTSTATE_CONNECTED:
                self.Disconnect()
            if self.scriptState == axscript.SCRIPTSTATE_DISCONNECTED:
                self.Reset()
            self.Run()
            self.ChangeScriptState(axscript.SCRIPTSTATE_STARTED)
        elif state == axscript.SCRIPTSTATE_CONNECTED:
            if self.scriptState in [
                axscript.SCRIPTSTATE_UNINITIALIZED,
                axscript.SCRIPTSTATE_INITIALIZED,
            ]:
                self.ChangeScriptState(
                    axscript.SCRIPTSTATE_STARTED
                )  # report transition through started
                self.Run()
            if self.scriptState == axscript.SCRIPTSTATE_STARTED:
                self.Connect()
                self.ChangeScriptState(state)
        elif state == axscript.SCRIPTSTATE_DISCONNECTED:
            if self.scriptState == axscript.SCRIPTSTATE_CONNECTED:
                self.Disconnect()
        elif state == axscript.SCRIPTSTATE_CLOSED:
            self.Close()
        elif state == axscript.SCRIPTSTATE_UNINITIALIZED:
            if self.scriptState == axscript.SCRIPTSTATE_STARTED:
                self.Stop()
            if self.scriptState == axscript.SCRIPTSTATE_CONNECTED:
                self.Disconnect()
            if self.scriptState == axscript.SCRIPTSTATE_DISCONNECTED:
                self.Reset()
            self.ChangeScriptState(state)
        else:
            raise COMException(scode=winerror.E_INVALIDARG)

    def GetScriptState(self):
        return self.scriptState

    def Close(self):
        # 051135.python.framework.line840.comment trace("Close")
        if self.scriptState in [
            axscript.SCRIPTSTATE_CONNECTED,
            axscript.SCRIPTSTATE_DISCONNECTED,
        ]:
            self.Stop()
        if self.scriptState in [
            axscript.SCRIPTSTATE_CONNECTED,
            axscript.SCRIPTSTATE_DISCONNECTED,
            axscript.SCRIPTSTATE_INITIALIZED,
            axscript.SCRIPTSTATE_STARTED,
        ]:
            pass  # engine.close??
        if self.scriptState in [
            axscript.SCRIPTSTATE_UNINITIALIZED,
            axscript.SCRIPTSTATE_CONNECTED,
            axscript.SCRIPTSTATE_DISCONNECTED,
            axscript.SCRIPTSTATE_INITIALIZED,
            axscript.SCRIPTSTATE_STARTED,
        ]:
            self.ChangeScriptState(axscript.SCRIPTSTATE_CLOSED)
            # 051137.python.framework.line861.comment Completely reset all named items (including persistent)
            for item in self.subItems.values():
                item.Close()
            self.subItems = {}
            self.baseThreadId = -1
        if self.debugManager:
            self.debugManager.Close()
            self.debugManager = None
        self.scriptSite = None
        self.scriptCodeBlocks = {}
        self.persistLoaded = 0

    def AddNamedItem(self, name, flags):
        if self.scriptSite is None:
            raise COMException(scode=winerror.E_INVALIDARG)
        try:
            unknown = self.scriptSite.GetItemInfo(name, axscript.SCRIPTINFO_IUNKNOWN)[0]
            dispatch = unknown.QueryInterface(pythoncom.IID_IDispatch)
        except pythoncom.com_error:
            raise COMException(
                scode=winerror.E_NOINTERFACE,
                desc="Object has no dispatch interface available.",
            )
        newItem = self.subItems[name] = self.GetNamedItemClass()(
            self, name, dispatch, flags
        )
        if newItem.IsGlobal():
            newItem.CreateConnections()

    def GetScriptDispatch(self, name):
        # 051138.python.framework.line891.comment Base classes should override.
        raise COMException(scode=winerror.E_NOTIMPL)

    def GetCurrentScriptThreadID(self):
        return self.baseThreadId

    def GetScriptThreadID(self, win32ThreadId):
        if self.baseThreadId == -1:
            raise COMException(scode=winerror.E_UNEXPECTED)
        if self.baseThreadId != win32ThreadId:
            raise COMException(scode=winerror.E_INVALIDARG)
        return self.baseThreadId

    def GetScriptThreadState(self, scriptThreadId):
        if self.baseThreadId == -1:
            raise COMException(scode=winerror.E_UNEXPECTED)
        if scriptThreadId != self.baseThreadId:
            raise COMException(scode=winerror.E_INVALIDARG)
        return self.threadState

    def AddTypeLib(self, uuid, major, minor, flags):
        # 051139.python.framework.line912.comment Get the win32com gencache to register this library.
        from win32com.client import gencache

        gencache.EnsureModule(uuid, self.lcid, major, minor, bForDemand=1)

    # 051140.python.framework.line917.comment This is never called by the C++ framework - it does magic.
    # 051141.python.framework.line918.comment See PyGActiveScript.cpp
    # 051142.python.framework.line919.comment def InterruptScriptThread(self, stidThread, exc_info, flags):
    # 051143.python.framework.line920.comment raise COMException("Not Implemented", scode=winerror.E_NOTIMPL)

    def Clone(self):
        raise COMException("Not Implemented", scode=winerror.E_NOTIMPL)

    # 051144.python.framework.line925.comment
    # 051145.python.framework.line926.comment IObjectSafety

    # 051146.python.framework.line928.comment Note that IE seems to insist we say we support all the flags, even tho
    # 051147.python.framework.line929.comment we don't accept them all.  If unknown flags come in, they are ignored, and never
    # 051148.python.framework.line930.comment reflected in GetInterfaceSafetyOptions and the QIs obviously fail, but still IE
    # 051149.python.framework.line931.comment allows our engine to initialize.
    def SetInterfaceSafetyOptions(self, iid, optionsMask, enabledOptions):
        # 051150.python.framework.line933.comment trace ("SetInterfaceSafetyOptions", iid, optionsMask, enabledOptions)
        if optionsMask & enabledOptions == 0:
            return

        # 051151.python.framework.line937.comment See comments above.
        # 051152.python.framework.line938.comment if (optionsMask & enabledOptions & \
        # 051153.python.framework.line939.comment ~(axscript.INTERFACESAFE_FOR_UNTRUSTED_DATA | axscript.INTERFACESAFE_FOR_UNTRUSTED_CALLER)):
        # 051154.python.framework.line940.comment # request for options we don't understand
        # 051155.python.framework.line941.comment RaiseAssert(scode=winerror.E_FAIL, desc="Unknown safety options")

        if iid in [
            pythoncom.IID_IPersist,
            pythoncom.IID_IPersistStream,
            pythoncom.IID_IPersistStreamInit,
            axscript.IID_IActiveScript,
            axscript.IID_IActiveScriptParse,
        ]:
            supported = self._GetSupportedInterfaceSafetyOptions()
            self.safetyOptions = supported & optionsMask & enabledOptions
        else:
            raise COMException(scode=winerror.E_NOINTERFACE)

    def _GetSupportedInterfaceSafetyOptions(self):
        return 0

    def GetInterfaceSafetyOptions(self, iid):
        if iid in [
            pythoncom.IID_IPersist,
            pythoncom.IID_IPersistStream,
            pythoncom.IID_IPersistStreamInit,
            axscript.IID_IActiveScript,
            axscript.IID_IActiveScriptParse,
        ]:
            supported = self._GetSupportedInterfaceSafetyOptions()
            return supported, self.safetyOptions
        else:
            raise COMException(scode=winerror.E_NOINTERFACE)

    # 051156.python.framework.line971.comment
    # 051157.python.framework.line972.comment Other helpers.
    def ExecutePendingScripts(self):
        self.RegisterNewNamedItems()
        self.DoExecutePendingScripts()

    def ProcessScriptItemEvent(self, item, event, lcid, wFlags, args):
        # 051158.python.framework.line978.comment trace("ProcessScriptItemEvent", item, event, lcid, wFlags, args)
        self.RegisterNewNamedItems()
        return self.DoProcessScriptItemEvent(item, event, lcid, wFlags, args)

    def _DumpNamedItems_(self):
        for item in self.subItems.values():
            item._dump_(0)

    def ResetNamedItems(self):
        # 051159.python.framework.line987.comment Due to the way we work, we re-create persistent ones.
        existing = self.subItems
        self.subItems = {}
        for item in existing.values():
            item.Close()
            if item.flags & axscript.SCRIPTITEM_ISPERSISTENT:
                self.AddNamedItem(item.name, item.flags)

    def GetCurrentSafetyOptions(self):
        return self.safetyOptions

    def ProcessNewNamedItemsConnections(self):
        # 051160.python.framework.line999.comment Process all sub-items.
        for item in self.subItems.values():
            if not item.createdConnections:  # Fast-track!
                item.CreateConnections()

    def RegisterNewNamedItems(self):
        # 051162.python.framework.line1005.comment Register all sub-items.
        for item in self.subItems.values():
            if not item.isRegistered:  # Fast-track!
                self.RegisterNamedItem(item)

    def RegisterNamedItem(self, item):
        item.Register()

    def CheckConnectedOrDisconnected(self):
        if self.scriptState in [
            axscript.SCRIPTSTATE_CONNECTED,
            axscript.SCRIPTSTATE_DISCONNECTED,
        ]:
            return
        RaiseAssert(
            winerror.E_UNEXPECTED,
            "Not connected or disconnected - %d" % self.scriptState,
        )

    def Connect(self):
        self.ProcessNewNamedItemsConnections()
        self.RegisterNewNamedItems()
        self.ConnectEventHandlers()

    def Run(self):
        # 051164.python.framework.line1030.comment trace("AXScript running...")
        if (
            self.scriptState != axscript.SCRIPTSTATE_INITIALIZED
            and self.scriptState != axscript.SCRIPTSTATE_STARTED
        ):
            raise COMException(scode=winerror.E_UNEXPECTED)
        # 051165.python.framework.line1036.comment self._DumpNamedItems_()
        self.ExecutePendingScripts()
        self.DoRun()

    def Stop(self):
        # 051166.python.framework.line1041.comment Stop all executing scripts, and disconnect.
        if self.scriptState == axscript.SCRIPTSTATE_CONNECTED:
            self.Disconnect()
        # 051167.python.framework.line1044.comment Reset back to initialized.
        self.Reset()

    def Disconnect(self):
        self.CheckConnectedOrDisconnected()
        try:
            self.DisconnectEventHandlers()
        except pythoncom.com_error:
            # 051168.python.framework.line1052.comment Ignore errors when disconnecting.
            pass

        self.ChangeScriptState(axscript.SCRIPTSTATE_DISCONNECTED)

    def ConnectEventHandlers(self):
        # 051169.python.framework.line1058.comment trace ("Connecting to event handlers")
        for item in self.subItems.values():
            item.Connect()
        self.ChangeScriptState(axscript.SCRIPTSTATE_CONNECTED)

    def DisconnectEventHandlers(self):
        # 051170.python.framework.line1064.comment trace ("Disconnecting from event handlers")
        for item in self.subItems.values():
            item.Disconnect()

    def Reset(self):
        # 051171.python.framework.line1069.comment Keeping persistent engine state, reset back an initialized state
        self.ResetNamedItems()
        self.ChangeScriptState(axscript.SCRIPTSTATE_INITIALIZED)

    def ChangeScriptState(self, state):
        # 051172.python.framework.line1074.comment print(f"  ChangeScriptState with {state_map.get(state)} - currentstate = {state_map.get(self.scriptState)}")
        self.DisableInterrupts()
        try:
            self.scriptState = state
            try:
                if self.scriptSite:
                    self.scriptSite.OnStateChange(state)
            except pythoncom.com_error as xxx_todo_changeme:
                (hr, desc, exc, arg) = xxx_todo_changeme.args
        finally:
            self.EnableInterrupts()

    # 051173.python.framework.line1086.comment This stack frame is debugged - therefore we do as little as possible in it.
    def _ApplyInScriptedSection(self, fn, args):
        if self.debugManager:
            self.debugManager.OnEnterScript()
            if self.debugManager.adb.appDebugger:
                return self.debugManager.adb.runcall(fn, *args)
            else:
                return fn(*args)
        else:
            return fn(*args)

    def ApplyInScriptedSection(self, codeBlock: AXScriptCodeBlock | None, fn, args):
        self.BeginScriptedSection()
        try:
            try:
                # 051174.python.framework.line1101.comment print("ApplyInSS", codeBlock, fn, args)
                return self._ApplyInScriptedSection(fn, args)
            finally:
                if self.debugManager:
                    self.debugManager.OnLeaveScript()
                self.EndScriptedSection()
        except:
            self.HandleException(codeBlock)

    # 051175.python.framework.line1110.comment This stack frame is debugged - therefore we do as little as possible in it.
    def _CompileInScriptedSection(self, code, name, type):
        if self.debugManager:
            self.debugManager.OnEnterScript()
        return compile(code, name, type)

    def CompileInScriptedSection(
        self, codeBlock: AXScriptCodeBlock, type, realCode=None
    ):
        if codeBlock.codeObject is not None:  # already compiled
            return 1
        if realCode is None:
            code = codeBlock.codeText
        else:
            code = realCode
        name = codeBlock.GetFileName()
        self.BeginScriptedSection()
        try:
            try:
                codeObject = self._CompileInScriptedSection(RemoveCR(code), name, type)
                codeBlock.codeObject = codeObject
                return 1
            finally:
                if self.debugManager:
                    self.debugManager.OnLeaveScript()
                self.EndScriptedSection()
        except:
            self.HandleException(codeBlock)

    # 051177.python.framework.line1139.comment This stack frame is debugged - therefore we do as little as possible in it.
    def _ExecInScriptedSection(self, codeObject, globals, locals=None):
        if self.debugManager:
            self.debugManager.OnEnterScript()
            if self.debugManager.adb.appDebugger:
                return self.debugManager.adb.run(codeObject, globals, locals)
            else:
                exec(codeObject, globals, locals)
        else:
            exec(codeObject, globals, locals)

    def ExecInScriptedSection(self, codeBlock: AXScriptCodeBlock, globals, locals=None):
        if locals is None:
            locals = globals
        assert not codeBlock.beenExecuted, (
            "This code block should not have been executed"
        )
        codeBlock.beenExecuted = 1
        self.BeginScriptedSection()
        try:
            try:
                self._ExecInScriptedSection(codeBlock.codeObject, globals, locals)
            finally:
                if self.debugManager:
                    self.debugManager.OnLeaveScript()
                self.EndScriptedSection()
        except:
            self.HandleException(codeBlock)

    def _EvalInScriptedSection(self, codeBlock, globals, locals=None):
        if self.debugManager:
            self.debugManager.OnEnterScript()
            if self.debugManager.adb.appDebugger:
                return self.debugManager.adb.runeval(codeBlock, globals, locals)
            else:
                return eval(codeBlock, globals, locals)
        else:
            return eval(codeBlock, globals, locals)

    def EvalInScriptedSection(self, codeBlock, globals, locals=None):
        if locals is None:
            locals = globals
        assert not codeBlock.beenExecuted, (
            "This code block should not have been executed"
        )
        codeBlock.beenExecuted = 1
        self.BeginScriptedSection()
        try:
            try:
                return self._EvalInScriptedSection(
                    codeBlock.codeObject, globals, locals
                )
            finally:
                if self.debugManager:
                    self.debugManager.OnLeaveScript()
                self.EndScriptedSection()
        except:
            self.HandleException(codeBlock)

    def HandleException(self, codeBlock: AXScriptCodeBlock | None) -> NoReturn:
        """Never returns - raises a ComException"""
        exc_type, exc_value, *_ = sys.exc_info()
        # 051178.python.framework.line1201.comment If a SERVER exception, re-raise it.  If a client side COM error, it is
        # 051179.python.framework.line1202.comment likely to have originated from the script code itself, and therefore
        # 051180.python.framework.line1203.comment needs to be reported like any other exception.
        if IsCOMServerException(exc_type):
            # 051181.python.framework.line1205.comment Ensure the traceback doesn't cause a cycle.
            raise
        # 051182.python.framework.line1207.comment It could be an error by another script.
        if (
            isinstance(exc_value, pythoncom.com_error)
            and exc_value.hresult == axscript.SCRIPT_E_REPORTED
        ):
            # 051183.python.framework.line1212.comment Ensure the traceback doesn't cause a cycle.
            raise COMException(scode=exc_value.hresult)

        exception = error.AXScriptException(self, codeBlock, exc_value=exc_value)

        # 051184.python.framework.line1217.comment Ensure the traceback doesn't cause a cycle.
        result_exception = error.ProcessAXScriptException(
            self.scriptSite, self.debugManager, exception
        )
        if result_exception is not None:
            try:
                self.scriptSite.OnScriptTerminate(None, result_exception)
            except pythoncom.com_error:
                pass  # Ignore errors telling engine we stopped.
            # 051186.python.framework.line1226.comment reset ourselves to 'connected' so further events continue to fire.
            self.SetScriptState(axscript.SCRIPTSTATE_CONNECTED)
            raise result_exception
        # 051187.python.framework.line1229.comment I think that in some cases this should just return - but the code
        # 051188.python.framework.line1230.comment that could return None above is disabled, so it never happens.
        RaiseAssert(
            winerror.E_UNEXPECTED, "Don't have an exception to raise to the caller!"
        )

    def BeginScriptedSection(self):
        if self.scriptSite is None:
            raise COMException(scode=winerror.E_UNEXPECTED)
        self.scriptSite.OnEnterScript()

    def EndScriptedSection(self):
        if self.scriptSite is None:
            raise COMException(scode=winerror.E_UNEXPECTED)
        self.scriptSite.OnLeaveScript()

    def DisableInterrupts(self):
        pass

    def EnableInterrupts(self):
        pass

    def GetNamedItem(self, name):
        try:
            return self.subItems[name]
        except KeyError:
            raise COMException(scode=winerror.E_INVALIDARG)

    def GetNamedItemClass(self):
        return ScriptItem

    def _AddScriptCodeBlock(self, codeBlock):
        self.scriptCodeBlocks[codeBlock.GetFileName()] = codeBlock
        if self.debugManager:
            self.debugManager.AddScriptBlock(codeBlock)


if __name__ == "__main__":
    print("This is a framework class - please use pyscript.py etc")


def dumptypeinfo(typeinfo):
    return
    attr = typeinfo.GetTypeAttr()
    # 051189.python.framework.line1273.comment Loop over all methods
    print("Methods")
    for j in range(attr[6]):
        fdesc = list(typeinfo.GetFuncDesc(j))
        id = fdesc[0]
        try:
            names = typeinfo.GetNames(id)
        except pythoncom.ole_error:
            names = None
        doc = typeinfo.GetDocumentation(id)

        print(" ", names, "has attr", fdesc)

    # 051190.python.framework.line1286.comment Loop over all variables (ie, properties)
    print("Variables")
    for j in range(attr[7]):
        fdesc = list(typeinfo.GetVarDesc(j))
        names = typeinfo.GetNames(id)
        print(" ", names, "has attr", fdesc)
