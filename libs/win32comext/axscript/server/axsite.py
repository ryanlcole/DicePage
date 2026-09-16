import pythoncom
import winerror
from win32com.axscript import axscript
from win32com.server import util
from win32com.server.exception import COMException


class AXEngine:
    def __init__(self, site, engine):
        self.eScript = self.eParse = self.eSafety = None
        if isinstance(engine, str):
            engine = pythoncom.CoCreateInstance(
                engine, None, pythoncom.CLSCTX_SERVER, pythoncom.IID_IUnknown
            )

        self.eScript = engine.QueryInterface(axscript.IID_IActiveScript)
        self.eParse = engine.QueryInterface(axscript.IID_IActiveScriptParse)
        self.eSafety = engine.QueryInterface(axscript.IID_IObjectSafety)

        self.eScript.SetScriptSite(site)
        self.eParse.InitNew()

    def __del__(self):
        self.Close()

    def GetScriptDispatch(self, name=None):
        return self.eScript.GetScriptDispatch(name)

    def AddNamedItem(self, item, flags):
        return self.eScript.AddNamedItem(item, flags)

    # 051282.python.axsite.line32.comment Some helpers.
    def AddCode(self, code, flags=0):
        self.eParse.ParseScriptText(code, None, None, None, 0, 0, flags)

    def EvalCode(self, code):
        return self.eParse.ParseScriptText(
            code, None, None, None, 0, 0, axscript.SCRIPTTEXT_ISEXPRESSION
        )

    def Start(self):
        # 051283.python.axsite.line42.comment Should maybe check state?
        # 051284.python.axsite.line43.comment Do I need to transition through?
        self.eScript.SetScriptState(axscript.SCRIPTSTATE_STARTED)

    # 051285.python.axsite.line46.comment self.eScript.SetScriptState(axscript.SCRIPTSTATE_CONNECTED)

    def Close(self):
        if self.eScript:
            self.eScript.Close()
        self.eScript = self.eParse = self.eSafety = None

    def SetScriptState(self, state):
        self.eScript.SetScriptState(state)


IActiveScriptSite_methods = [
    "GetLCID",
    "GetItemInfo",
    "GetDocVersionString",
    "OnScriptTerminate",
    "OnStateChange",
    "OnScriptError",
    "OnEnterScript",
    "OnLeaveScript",
]


class AXSite:
    """An Active Scripting site.  A Site can have exactly one engine."""

    _public_methods_ = IActiveScriptSite_methods
    _com_interfaces_ = [axscript.IID_IActiveScriptSite]

    def __init__(self, objModel={}, engine=None, lcid=0):
        self.lcid = lcid
        self.objModel = {}
        for name, object in objModel.items():
            # 051286.python.axsite.line79.comment Gregs code did str.lower this - I think that is callers job if he wants!
            self.objModel[name] = object

        self.engine = None
        if engine:
            self._AddEngine(engine)

    def AddEngine(self, engine):
        """Adds a new engine to the site.
        engine can be a string, or a fully wrapped engine object.
        """
        if isinstance(engine, str):
            newEngine = AXEngine(util.wrap(self), engine)
        else:
            newEngine = engine
        self.engine = newEngine
        flags = (
            axscript.SCRIPTITEM_ISVISIBLE
            | axscript.SCRIPTITEM_NOCODE
            | axscript.SCRIPTITEM_GLOBALMEMBERS
            | axscript.SCRIPTITEM_ISPERSISTENT
        )
        for name in self.objModel:
            newEngine.AddNamedItem(name, flags)
            newEngine.SetScriptState(axscript.SCRIPTSTATE_INITIALIZED)
        return newEngine

    # 051287.python.axsite.line106.comment B/W compat
    _AddEngine = AddEngine

    def _Close(self):
        self.engine.Close()
        self.objModel = {}

    def GetLCID(self):
        return self.lcid

    def GetItemInfo(self, name, returnMask):
        if name not in self.objModel:
            raise COMException(
                scode=winerror.TYPE_E_ELEMENTNOTFOUND, desc="item not found"
            )

        # 051288.python.axsite.line122.comment ## for now, we don't have any type information

        if returnMask & axscript.SCRIPTINFO_IUNKNOWN:
            return (self.objModel[name], None)

        return (None, None)

    def GetDocVersionString(self):
        return "Python AXHost version 1.0"

    def OnScriptTerminate(self, result, excepInfo):
        pass

    def OnStateChange(self, state):
        pass

    def OnScriptError(self, errorInterface):
        return winerror.S_FALSE

    def OnEnterScript(self):
        pass

    def OnLeaveScript(self):
        pass
