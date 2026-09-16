"""Support for stack-frames.

Provides Implements a nearly complete wrapper for a stack frame.
"""

import pythoncom

from . import axdebug, expressions, gateways
from .util import RaiseNotImpl, _wrap, trace

# 050923.python.stackframe.line11.comment def trace(*args):
# 050924.python.stackframe.line12.comment pass


class EnumDebugStackFrames(gateways.EnumDebugStackFrames):
    """A class that given a debugger object, can return an enumerator
    of DebugStackFrame objects.
    """

    def __init__(self, debugger):
        infos = []
        frame = debugger.currentframe
        # 050925.python.stackframe.line23.comment print("Stack check")
        while frame:
            # 050926.python.stackframe.line25.comment print(" Checking frame", frame.f_code.co_filename, frame.f_lineno-1, frame.f_trace)
            # 050927.python.stackframe.line26.comment Get a DebugCodeContext for the stack frame.  If we fail, then it
            # 050928.python.stackframe.line27.comment is not debuggable, and therefore not worth displaying.
            cc = debugger.codeContainerProvider.FromFileName(frame.f_code.co_filename)
            if cc is not None:
                try:
                    address = frame.f_locals["__axstack_address__"]
                except KeyError:
                    # 050929.python.stackframe.line33.comment print("Couldn't find stack address for",frame.f_code.co_filename, frame.f_lineno-1)
                    # 050930.python.stackframe.line34.comment Use this one, even tho it is wrong :-(
                    address = axdebug.GetStackAddress()
                frameInfo = (
                    DebugStackFrame(frame, frame.f_lineno - 1, cc),
                    address,
                    address + 1,
                    0,
                    None,
                )
                infos.append(frameInfo)
            # 050931.python.stackframe.line44.comment print("- Kept!")
            # 050932.python.stackframe.line45.comment else:
            # 050933.python.stackframe.line46.comment print("- rejected")
            frame = frame.f_back

        gateways.EnumDebugStackFrames.__init__(self, infos, 0)

    # 050934.python.stackframe.line51.comment def __del__(self):
    # 050935.python.stackframe.line52.comment print("EnumDebugStackFrames dieing")

    def Next(self, count):
        return gateways.EnumDebugStackFrames.Next(self, count)

    # 050936.python.stackframe.line57.comment def _query_interface_(self, iid):
    # 050937.python.stackframe.line58.comment from win32com.util import IIDToInterfaceName
    # 050938.python.stackframe.line59.comment print(f"EnumDebugStackFrames QI with {IIDToInterfaceName(iid)} ({iid})")
    # 050939.python.stackframe.line60.comment return 0
    def _wrap(self, obj):
        # 050940.python.stackframe.line62.comment This enum returns a tuple, with 2 com objects in it.
        obFrame, min, lim, fFinal, obFinal = obj
        obFrame = _wrap(obFrame, axdebug.IID_IDebugStackFrame)
        if obFinal:
            obFinal = _wrap(obFinal, pythoncom.IID_IUnknown)
        return obFrame, min, lim, fFinal, obFinal


class DebugStackFrame(gateways.DebugStackFrame):
    def __init__(self, frame, lineno, codeContainer):
        self.frame = frame
        self.lineno = lineno
        self.codeContainer = codeContainer
        self.expressionContext = None

    # 050941.python.stackframe.line77.comment def __del__(self):
    # 050942.python.stackframe.line78.comment print("DSF dieing")
    def _query_interface_(self, iid):
        if iid == axdebug.IID_IDebugExpressionContext:
            if self.expressionContext is None:
                self.expressionContext = _wrap(
                    expressions.ExpressionContext(self.frame),
                    axdebug.IID_IDebugExpressionContext,
                )
            return self.expressionContext
        # 050943.python.stackframe.line87.comment from win32com.util import IIDToInterfaceName
        # 050944.python.stackframe.line88.comment print(f"DebugStackFrame QI with {IIDToInterfaceName(iid)} ({iid})")
        return 0

    # 050945.python.stackframe.line91.comment
    # 050946.python.stackframe.line92.comment The following need implementation
    def GetThread(self):
        """Returns the thread associated with this stack frame.

        Result must be a IDebugApplicationThread
        """
        RaiseNotImpl("GetThread")

    def GetCodeContext(self):
        offset = self.codeContainer.GetPositionOfLine(self.lineno)
        return self.codeContainer.GetCodeContextAtPosition(offset)

    # 050947.python.stackframe.line104.comment
    # 050948.python.stackframe.line105.comment The following are usefully implemented
    def GetDescriptionString(self, fLong):
        filename = self.frame.f_code.co_filename
        s = ""
        if 0:  # fLong:
            s += filename
        if self.frame.f_code.co_name:
            s += self.frame.f_code.co_name
        else:
            s += "<lambda>"
        return s

    def GetLanguageString(self, fLong):
        if fLong:
            return "Python ActiveX Scripting Engine"
        else:
            return "Python"

    def GetDebugProperty(self):
        return _wrap(StackFrameDebugProperty(self.frame), axdebug.IID_IDebugProperty)


class DebugStackFrameSniffer:
    _public_methods_ = ["EnumStackFrames"]
    _com_interfaces_ = [axdebug.IID_IDebugStackFrameSniffer]

    def __init__(self, debugger):
        self.debugger = debugger
        trace("DebugStackFrameSniffer instantiated")

    # 050950.python.stackframe.line135.comment def __del__(self):
    # 050951.python.stackframe.line136.comment print("DSFS dieing")
    def EnumStackFrames(self):
        trace("DebugStackFrameSniffer.EnumStackFrames called")
        return _wrap(
            EnumDebugStackFrames(self.debugger), axdebug.IID_IEnumDebugStackFrames
        )


# 050952.python.stackframe.line144.comment A DebugProperty for a stack frame.
class StackFrameDebugProperty:
    _com_interfaces_ = [axdebug.IID_IDebugProperty]
    _public_methods_ = [
        "GetPropertyInfo",
        "GetExtendedInfo",
        "SetValueAsString",
        "EnumMembers",
        "GetParent",
    ]

    def __init__(self, frame):
        self.frame = frame

    def GetPropertyInfo(self, dwFieldSpec, nRadix):
        RaiseNotImpl("StackFrameDebugProperty::GetPropertyInfo")

    def GetExtendedInfo(self):  ### Note - not in the framework.
        RaiseNotImpl("StackFrameDebugProperty::GetExtendedInfo")

    def SetValueAsString(self, value, radix):
        # 050954.python.stackframe.line165.comment
        RaiseNotImpl("DebugProperty::SetValueAsString")

    def EnumMembers(self, dwFieldSpec, nRadix, iid):
        print("EnumMembers", dwFieldSpec, nRadix, iid)
        from . import expressions

        return expressions.MakeEnumDebugProperty(
            self.frame.f_locals, dwFieldSpec, nRadix, iid, self.frame
        )

    def GetParent(self):
        # 050955.python.stackframe.line177.comment return IDebugProperty
        RaiseNotImpl("DebugProperty::GetParent")
