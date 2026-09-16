# 050956.python.util.line1.comment Utility function for wrapping objects.  Centralising allows me to turn
# 050957.python.util.line2.comment debugging on and off for the entire package in a single spot.

import os
import sys
import traceback

import win32api
import win32com.server.dispatcher
import win32com.server.policy
import win32com.server.util
import winerror
from win32com.server.exception import COMException

debugging = "DEBUG_AXDEBUG" in os.environ


def trace(*args):
    if not debugging:
        return
    print(str(win32api.GetCurrentThreadId()) + ":", end=" ")
    for arg in args:
        print(arg, end=" ")
    print()


# 050958.python.util.line27.comment The AXDebugging implementation assumes that the returned COM pointers are in
# 050959.python.util.line28.comment some cases identical.  Eg, from a C++ perspective:
# 050960.python.util.line29.comment p->GetSomeInterface( &p1 );
# 050961.python.util.line30.comment p->GetSomeInterface( &p2 );
# 050962.python.util.line31.comment p1==p2
# 050963.python.util.line32.comment By default, this is _not_ true for Python.
# 050964.python.util.line33.comment (Now this is only true for Document objects, and Python
# 050965.python.util.line34.comment now does ensure this.


def _wrap(object, iid):
    useDispatcher = win32com.server.policy.DispatcherWin32trace if debugging else None
    return win32com.server.util.wrap(object, iid, useDispatcher=useDispatcher)


def RaiseNotImpl(who=None):
    if who is not None:
        print(f"********* Function {who} Raising E_NOTIMPL  ************")

    # 050966.python.util.line46.comment Print a sort-of "traceback", dumping all the frames leading to here.
    for frame, i in traceback.walk_stack(sys._getframe()):
        print(f"File: {frame.f_code.co_filename}, Line: {frame.f_lineno}")

    # 050967.python.util.line50.comment and raise the exception for COM
    raise COMException(scode=winerror.E_NOTIMPL)


class Dispatcher(win32com.server.dispatcher.DispatcherWin32trace):
    def __init__(self, policyClass, object):
        win32com.server.dispatcher.DispatcherTrace.__init__(self, policyClass, object)
        import win32traceutil  # Sets up everything.

    # 050969.python.util.line59.comment print(f"Object with win32trace dispatcher created ({object})")

    def _QueryInterface_(self, iid):
        rc = win32com.server.policy.DispatcherBase._QueryInterface_(self, iid)
        # 050970.python.util.line63.comment if not rc:
        # 050971.python.util.line64.comment self._trace_(f"in _QueryInterface_ with unsupported IID {IIDToInterfaceName(iid)} ({iid})\n")
        return rc

    def _Invoke_(self, dispid, lcid, wFlags, args):
        print(
            "In Invoke with",
            dispid,
            lcid,
            wFlags,
            args,
            "with object",
            self.policy._obj_,
        )
        try:
            rc = win32com.server.policy.DispatcherBase._Invoke_(
                self, dispid, lcid, wFlags, args
            )
            # 050972.python.util.line81.comment print("Invoke of", dispid, "returning", rc)
            return rc
        except COMException:
            t, v, tb = sys.exc_info()
            tb = None  # A cycle
            scode = v.scode
            try:
                desc = f" ({v.description})"
            except AttributeError:
                desc = ""
            print(f"*** Invoke of {dispid} raised COM exception 0x{scode:x}{desc}")
        except:
            print(f"*** Invoke of {dispid} failed:")
            typ, val, tb = sys.exc_info()
            import traceback

            traceback.print_exception(typ, val, tb)
            raise
