"""A module for managing the AXDebug I*Contexts"""

from . import adb, axdebug, gateways

# 050825.python.contexts.line5.comment Utility function for wrapping object created by this module.
from .util import _wrap


class DebugCodeContext(gateways.DebugCodeContext, gateways.DebugDocumentContext):
    # 050826.python.contexts.line10.comment NOTE: We also implement the IDebugDocumentContext interface for Simple Hosts.
    # 050827.python.contexts.line11.comment Thus, debugDocument may be NULL when we have smart hosts - but in that case, we
    # 050828.python.contexts.line12.comment won't be called upon to provide it.
    _public_methods_ = (
        gateways.DebugCodeContext._public_methods_
        + gateways.DebugDocumentContext._public_methods_
    )
    _com_interfaces_ = (
        gateways.DebugCodeContext._com_interfaces_
        + gateways.DebugDocumentContext._com_interfaces_
    )

    def __init__(self, lineNo, charPos, len, codeContainer, debugSite):
        self.debugSite = debugSite
        self.offset = charPos
        self.length = len
        self.breakPointState = 0
        self.lineno = lineNo
        gateways.DebugCodeContext.__init__(self)
        self.codeContainer = codeContainer

    def _Close(self):
        self.debugSite = None

    def GetDocumentContext(self):
        if self.debugSite is not None:
            # 050829.python.contexts.line36.comment We have a smart host - let him give it to us.
            return self.debugSite.GetDocumentContextFromPosition(
                self.codeContainer.sourceContext, self.offset, self.length
            )
        else:
            # 050830.python.contexts.line41.comment Simple host - Fine - I'll do it myself!
            return _wrap(self, axdebug.IID_IDebugDocumentContext)

    def SetBreakPoint(self, bps):
        self.breakPointState = bps
        adb.OnSetBreakPoint(self, bps, self.lineno)

    # 050831.python.contexts.line48.comment The DebugDocumentContext methods for simple hosts.
    def GetDocument(self):
        return self.codeContainer.debugDocument

    def EnumCodeContexts(self):
        return _wrap(EnumDebugCodeContexts([self]), axdebug.IID_IEnumDebugCodeContexts)


class EnumDebugCodeContexts(gateways.EnumDebugCodeContexts):
    def _wrap(self, obj):
        return _wrap(obj, axdebug.IID_IDebugCodeContext)
