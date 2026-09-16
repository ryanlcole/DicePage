"""The glue between the Python debugger interface and the Active Debugger interface"""

import _thread
import bdb
import os
import sys
import traceback

import pythoncom
import win32api
import win32com.client.connect
from win32com.axdebug.util import _wrap, trace

from . import axdebug, gateways, stackframe


def fnull(*args):
    pass


debugging = "DEBUG_AXDEBUG" in os.environ
traceenter = fnull  # trace enter of functions
tracev = fnull  # verbose trace

if debugging:
    traceenter = trace  # trace enter of functions
    tracev = trace  # verbose trace


class OutputReflector:
    def __init__(self, file, writefunc):
        self.writefunc = writefunc
        self.file = file

    def __getattr__(self, name):
        return getattr(self.file, name)

    def write(self, message):
        self.writefunc(message)
        self.file.write(message)


def _dumpf(frame):
    if frame is None:
        return "<None>"
    else:
        addn = "(with trace!)"
        if frame.f_trace is None:
            addn = " **No Trace Set **"
        return f"Frame at {id(frame)}, file {frame.f_code.co_filename}, line: {frame.f_lineno}{addn}"


g_adb = None


def OnSetBreakPoint(codeContext, breakPointState, lineNo):
    try:
        fileName = codeContext.codeContainer.GetFileName()
        # 050746.python.adb.line59.comment inject the code into linecache.
        import linecache

        linecache.cache[fileName] = 0, 0, codeContext.codeContainer.GetText(), fileName
        g_adb._OnSetBreakPoint(fileName, codeContext, breakPointState, lineNo + 1)
    except:
        traceback.print_exc()


class Adb(bdb.Bdb, gateways.RemoteDebugApplicationEvents):
    def __init__(self):
        self.debugApplication = None
        self.debuggingThread = None
        self.debuggingThreadStateHandle = None
        self.stackSnifferCookie = self.stackSniffer = None
        self.codeContainerProvider = None
        self.debuggingThread = None
        self.breakFlags = None
        self.breakReason = None
        self.appDebugger = None
        self.appEventConnection = None
        self.logicalbotframe = None  # Anything at this level or below does not exist!
        self.currentframe = None  # The frame we are currently in.
        self.recursiveData = []  # Data saved for each reentery on this thread.
        bdb.Bdb.__init__(self)
        self._threadprotectlock = _thread.allocate_lock()
        self.reset()

    def canonic(self, fname):
        if fname[0] == "<":
            return fname
        return bdb.Bdb.canonic(self, fname)

    def reset(self):
        traceenter("adb.reset")
        bdb.Bdb.reset(self)

    def __xxxxx__set_break(self, filename, lineno, cond=None):
        # 050750.python.adb.line97.comment As per standard one, except no linecache checking!
        if filename not in self.breaks:
            self.breaks[filename] = []
        list = self.breaks[filename]
        if lineno in list:
            return "There is already a breakpoint there!"
        list.append(lineno)
        if cond is not None:
            self.cbreaks[filename, lineno] = cond

    def stop_here(self, frame):
        traceenter("stop_here", _dumpf(frame), _dumpf(self.stopframe))
        # 050751.python.adb.line109.comment As per bdb.stop_here, except for logicalbotframe
        # 050752.python.adb.line110.comment if self.stopframe is None:
        # 050753.python.adb.line111.comment return 1
        if frame is self.stopframe:
            return 1

        tracev("stop_here said 'No'!")
        return 0

    def break_here(self, frame):
        traceenter("break_here", self.breakFlags, _dumpf(frame))
        self.breakReason = None
        if self.breakFlags == axdebug.APPBREAKFLAG_DEBUGGER_HALT:
            self.breakReason = axdebug.BREAKREASON_DEBUGGER_HALT
        elif self.breakFlags == axdebug.APPBREAKFLAG_DEBUGGER_BLOCK:
            self.breakReason = axdebug.BREAKREASON_DEBUGGER_BLOCK
        elif self.breakFlags == axdebug.APPBREAKFLAG_STEP:
            self.breakReason = axdebug.BREAKREASON_STEP
        else:
            print("Calling base 'break_here' with", self.breaks)
            if bdb.Bdb.break_here(self, frame):
                self.breakReason = axdebug.BREAKREASON_BREAKPOINT
        return self.breakReason is not None

    def break_anywhere(self, frame):
        traceenter("break_anywhere", _dumpf(frame))
        if self.breakFlags == axdebug.APPBREAKFLAG_DEBUGGER_HALT:
            self.breakReason = axdebug.BREAKREASON_DEBUGGER_HALT
            return 1
        rc = bdb.Bdb.break_anywhere(self, frame)
        tracev("break_anywhere", _dumpf(frame), "returning", rc)
        return rc

    def dispatch_return(self, frame, arg):
        traceenter("dispatch_return", _dumpf(frame), arg)
        if self.logicalbotframe is frame:
            # 050754.python.adb.line145.comment We don't want to debug parent frames.
            tracev("dispatch_return resetting sys.trace")
            sys.settrace(None)
            return
        # 050755.python.adb.line149.comment self.bSetTrace = 0
        self.currentframe = frame.f_back
        return bdb.Bdb.dispatch_return(self, frame, arg)

    def dispatch_line(self, frame):
        traceenter("dispatch_line", _dumpf(frame), _dumpf(self.botframe))
        # 050756.python.adb.line155.comment trace("logbotframe is", _dumpf(self.logicalbotframe), "botframe is", self.botframe)
        if frame is self.logicalbotframe:
            trace("dispatch_line", _dumpf(frame), "for bottom frame returing tracer")
            # 050757.python.adb.line158.comment The next code executed in the frame above may be a builtin (eg, apply())
            # 050758.python.adb.line159.comment in which sys.trace needs to be set.
            sys.settrace(self.trace_dispatch)
            # 050759.python.adb.line161.comment And return the tracer incase we are about to execute Python code,
            # 050760.python.adb.line162.comment in which case sys tracer is ignored!
            return self.trace_dispatch

        if self.codeContainerProvider.FromFileName(frame.f_code.co_filename) is None:
            trace(
                "dispatch_line has no document for", _dumpf(frame), "- skipping trace!"
            )
            return None
        self.currentframe = (
            frame  # So the stack sniffer knows our most recent, debuggable code.
        )
        return bdb.Bdb.dispatch_line(self, frame)

    def dispatch_call(self, frame, arg):
        traceenter("dispatch_call", _dumpf(frame))
        frame.f_locals["__axstack_address__"] = axdebug.GetStackAddress()
        if frame is self.botframe:
            trace("dispatch_call is self.botframe - returning tracer")
            return self.trace_dispatch
        # 050762.python.adb.line181.comment Not our bottom frame.  If we have a document for it,
        # 050763.python.adb.line182.comment then trace it, otherwise run at full speed.
        if self.codeContainerProvider.FromFileName(frame.f_code.co_filename) is None:
            trace(
                "dispatch_call has no document for", _dumpf(frame), "- skipping trace!"
            )
            # 050764.python.adb.line187.comment sys.settrace(None)
            return None
        return self.trace_dispatch

        # 050765.python.adb.line191.comment rc =  bdb.Bdb.dispatch_call(self, frame, arg)
        # 050766.python.adb.line192.comment trace("dispatch_call", _dumpf(frame),"returned",rc)
        # 050767.python.adb.line193.comment return rc

    def trace_dispatch(self, frame, event, arg):
        traceenter("trace_dispatch", _dumpf(frame), event, arg)
        if self.debugApplication is None:
            trace("trace_dispatch has no application!")
            return  # None
        return bdb.Bdb.trace_dispatch(self, frame, event, arg)

    # 050769.python.adb.line202.comment
    # 050770.python.adb.line203.comment The user functions do bugger all!
    # 050771.python.adb.line204.comment
    # 050772.python.adb.line205.comment def user_call(self, frame, argument_list):
    # 050773.python.adb.line206.comment traceenter("user_call",_dumpf(frame))

    def user_line(self, frame):
        traceenter("user_line", _dumpf(frame))
        # 050774.python.adb.line210.comment Traces at line zero
        if frame.f_lineno != 0:
            breakReason = self.breakReason
            if breakReason is None:
                breakReason = axdebug.BREAKREASON_STEP
            self._HandleBreakPoint(frame, None, breakReason)

    def user_return(self, frame, return_value):
        # 050775.python.adb.line218.comment traceenter("user_return",_dumpf(frame),return_value)
        bdb.Bdb.user_return(self, frame, return_value)

    def user_exception(self, frame, exc_info):
        # 050776.python.adb.line222.comment traceenter("user_exception")
        bdb.Bdb.user_exception(self, frame, exc_info)

    def _HandleBreakPoint(self, frame, tb, reason):
        traceenter(
            "Calling HandleBreakPoint with reason", reason, "at frame", _dumpf(frame)
        )
        traceenter(" Current frame is", _dumpf(self.currentframe))
        try:
            resumeAction = self.debugApplication.HandleBreakPoint(reason)
            tracev("HandleBreakPoint returned with ", resumeAction)
        except pythoncom.com_error as details:
            # 050777.python.adb.line234.comment Eeek - the debugger is dead, or something serious is happening.
            # 050778.python.adb.line235.comment Assume we should continue
            resumeAction = axdebug.BREAKRESUMEACTION_CONTINUE
            trace("HandleBreakPoint FAILED with", details)

        self.stack = []
        self.curindex = 0
        if resumeAction == axdebug.BREAKRESUMEACTION_ABORT:
            self.set_quit()
        elif resumeAction == axdebug.BREAKRESUMEACTION_CONTINUE:
            tracev("resume action is continue")
            self.set_continue()
        elif resumeAction == axdebug.BREAKRESUMEACTION_STEP_INTO:
            tracev("resume action is step")
            self.set_step()
        elif resumeAction == axdebug.BREAKRESUMEACTION_STEP_OVER:
            tracev("resume action is next")
            self.set_next(frame)
        elif resumeAction == axdebug.BREAKRESUMEACTION_STEP_OUT:
            tracev("resume action is stop out")
            self.set_return(frame)
        else:
            raise ValueError("unknown resume action flags")
        self.breakReason = None

    def set_trace(self):
        self.breakReason = axdebug.BREAKREASON_LANGUAGE_INITIATED
        bdb.Bdb.set_trace(self)

    def CloseApp(self):
        traceenter("ClosingApp")
        self.reset()
        self.logicalbotframe = None
        if self.stackSnifferCookie is not None:
            try:
                self.debugApplication.RemoveStackFrameSniffer(self.stackSnifferCookie)

            except pythoncom.com_error:
                trace(
                    f"*** Could not RemoveStackFrameSniffer {self.stackSnifferCookie}"
                )
        self.stackSnifferCookie = self.stackSniffer = None

        if self.appEventConnection is not None:
            self.appEventConnection.Disconnect()
            self.appEventConnection = None
        self.debugApplication = None
        self.appDebugger = None
        if self.codeContainerProvider is not None:
            self.codeContainerProvider.Close()
            self.codeContainerProvider = None

    def AttachApp(self, debugApplication, codeContainerProvider):
        # 050779.python.adb.line287.comment traceenter("AttachApp", debugApplication, codeContainerProvider)
        self.codeContainerProvider = codeContainerProvider
        self.debugApplication = debugApplication
        self.stackSniffer = _wrap(
            stackframe.DebugStackFrameSniffer(self), axdebug.IID_IDebugStackFrameSniffer
        )
        self.stackSnifferCookie = debugApplication.AddStackFrameSniffer(
            self.stackSniffer
        )
        # 050780.python.adb.line296.comment trace(f"StackFrameSniffer added ({self.stackSnifferCookie})")

        # 050781.python.adb.line298.comment Connect to the application events.
        self.appEventConnection = win32com.client.connect.SimpleConnection(
            self.debugApplication, self, axdebug.IID_IRemoteDebugApplicationEvents
        )

    def ResetAXDebugging(self):
        traceenter("ResetAXDebugging", self, "with refcount", len(self.recursiveData))
        if win32api.GetCurrentThreadId() != self.debuggingThread:
            trace("ResetAXDebugging called on other thread")
            return

        if len(self.recursiveData) == 0:
            # 050782.python.adb.line310.comment print("ResetAXDebugging called for final time.")
            self.logicalbotframe = None
            self.debuggingThread = None
            self.currentframe = None
            self.debuggingThreadStateHandle = None
            return

        (
            self.logbotframe,
            self.stopframe,
            self.currentframe,
            self.debuggingThreadStateHandle,
        ) = self.recursiveData[0]
        self.recursiveData = self.recursiveData[1:]

    def SetupAXDebugging(self, baseFrame=None, userFrame=None):
        """Get ready for potential debugging.  Must be called on the thread
        that is being debugged.
        """
        # 050783.python.adb.line329.comment userFrame is for non AXScript debugging.  This is the first frame of the
        # 050784.python.adb.line330.comment users code.
        if userFrame is None:
            userFrame = baseFrame
        else:
            # 050785.python.adb.line334.comment We have missed the "dispatch_call" function, so set this up now!
            userFrame.f_locals["__axstack_address__"] = axdebug.GetStackAddress()

        traceenter("SetupAXDebugging", self)
        self._threadprotectlock.acquire()
        try:
            thisThread = win32api.GetCurrentThreadId()
            if self.debuggingThread is None:
                self.debuggingThread = thisThread
            else:
                if self.debuggingThread != thisThread:
                    trace("SetupAXDebugging called on other thread - ignored!")
                    return
                # 050786.python.adb.line347.comment push our context.
                self.recursiveData.insert(
                    0,
                    (
                        self.logicalbotframe,
                        self.stopframe,
                        self.currentframe,
                        self.debuggingThreadStateHandle,
                    ),
                )
        finally:
            self._threadprotectlock.release()

        trace("SetupAXDebugging has base frame as", _dumpf(baseFrame))
        self.botframe = baseFrame
        self.stopframe = userFrame
        self.logicalbotframe = baseFrame
        self.currentframe = None
        self.debuggingThreadStateHandle = axdebug.GetThreadStateHandle()

        self._BreakFlagsChanged()

    # 050787.python.adb.line369.comment RemoteDebugApplicationEvents
    def OnConnectDebugger(self, appDebugger):
        traceenter("OnConnectDebugger", appDebugger)
        self.appDebugger = appDebugger
        # 050788.python.adb.line373.comment Reflect output to appDebugger
        writefunc = lambda s: appDebugger.onDebugOutput(s)
        sys.stdout = OutputReflector(sys.stdout, writefunc)
        sys.stderr = OutputReflector(sys.stderr, writefunc)

    def OnDisconnectDebugger(self):
        traceenter("OnDisconnectDebugger")
        # 050789.python.adb.line380.comment Stop reflecting output
        if isinstance(sys.stdout, OutputReflector):
            sys.stdout = sys.stdout.file
        if isinstance(sys.stderr, OutputReflector):
            sys.stderr = sys.stderr.file
        self.appDebugger = None
        self.set_quit()

    def OnSetName(self, name):
        traceenter("OnSetName", name)

    def OnDebugOutput(self, string):
        traceenter("OnDebugOutput", string)

    def OnClose(self):
        traceenter("OnClose")

    def OnEnterBreakPoint(self, rdat):
        traceenter("OnEnterBreakPoint", rdat)

    def OnLeaveBreakPoint(self, rdat):
        traceenter("OnLeaveBreakPoint", rdat)

    def OnCreateThread(self, rdat):
        traceenter("OnCreateThread", rdat)

    def OnDestroyThread(self, rdat):
        traceenter("OnDestroyThread", rdat)

    def OnBreakFlagChange(self, abf, rdat):
        traceenter("Debugger OnBreakFlagChange", abf, rdat)
        self.breakFlags = abf
        self._BreakFlagsChanged()

    def _BreakFlagsChanged(self):
        traceenter(
            f"_BreakFlagsChanged to {self.breakFlags} "
            + f"with our thread = {self.debuggingThread}, "
            + f"and debugging thread = {win32api.GetCurrentThreadId()}"
        )
        trace("_BreakFlagsChanged has breaks", self.breaks)
        # 050790.python.adb.line421.comment If a request comes on our debugging thread, then do it now!
        # 050791.python.adb.line422.comment if self.debuggingThread!=win32api.GetCurrentThreadId():
        # 050792.python.adb.line423.comment return

        if len(self.breaks) or self.breakFlags:
            if self.logicalbotframe:
                trace("BreakFlagsChange with bot frame", _dumpf(self.logicalbotframe))
                # 050793.python.adb.line428.comment We have frames not to be debugged (eg, Scripting engine frames
                # 050794.python.adb.line429.comment (sys.settrace will be set when out logicalbotframe is hit -
                # 050795.python.adb.line430.comment this may not be the right thing to do, as it may not cause the
                # 050796.python.adb.line431.comment immediate break we desire.)
                self.logicalbotframe.f_trace = self.trace_dispatch
            else:
                trace("BreakFlagsChanged, but no bottom frame")
                if self.stopframe is not None:
                    self.stopframe.f_trace = self.trace_dispatch
            # 050797.python.adb.line437.comment If we have the thread-state for the thread being debugged, then
            # 050798.python.adb.line438.comment we dynamically set its trace function - it is possible that the thread
            # 050799.python.adb.line439.comment being debugged is in a blocked call (eg, a message box) and we
            # 050800.python.adb.line440.comment want to hit the debugger the instant we return
        if (
            self.debuggingThreadStateHandle is not None
            and self.breakFlags
            and self.debuggingThread != win32api.GetCurrentThreadId()
        ):
            axdebug.SetThreadStateTrace(
                self.debuggingThreadStateHandle, self.trace_dispatch
            )

    def _OnSetBreakPoint(self, key, codeContext, bps, lineNo):
        traceenter("_OnSetBreakPoint", self, key, codeContext, bps, lineNo)
        if bps == axdebug.BREAKPOINT_ENABLED:
            problem = self.set_break(key, lineNo)
            if problem:
                print("*** set_break failed -", problem)
            trace("_OnSetBreakPoint just set BP and has breaks", self.breaks)
        else:
            self.clear_break(key, lineNo)
        self._BreakFlagsChanged()
        trace("_OnSetBreakPoint leaving with breaks", self.breaks)


def Debugger():
    global g_adb
    if g_adb is None:
        g_adb = Adb()
    return g_adb
