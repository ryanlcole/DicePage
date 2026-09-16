# 049858.python.errorSemantics.line1.comment errorSemantics.py

# 049859.python.errorSemantics.line3.comment Test the Python error handling semantics.  Specifically:
# 049860.python.errorSemantics.line4.comment
# 049861.python.errorSemantics.line5.comment * When a Python COM object is called via IDispatch, the nominated
# 049862.python.errorSemantics.line6.comment scode is placed in the exception tuple, and the HRESULT is
# 049863.python.errorSemantics.line7.comment DISP_E_EXCEPTION
# 049864.python.errorSemantics.line8.comment * When the same interface is called via IWhatever, the
# 049865.python.errorSemantics.line9.comment nominated  scode is returned directly (with the scode also
# 049866.python.errorSemantics.line10.comment reflected in the exception tuple)
# 049867.python.errorSemantics.line11.comment * In all cases, the description etc end up in the exception tuple
# 049868.python.errorSemantics.line12.comment * "Normal" Python exceptions resolve to an E_FAIL "internal error"

import pythoncom
import winerror
from win32com.client import Dispatch
from win32com.server.exception import COMException
from win32com.server.util import wrap
from win32com.test.util import CaptureWriter


# 049869.python.errorSemantics.line22.comment Our COM server.
class TestServer:
    _public_methods_ = ["Clone", "Commit", "LockRegion", "Read"]
    _com_interfaces_ = [pythoncom.IID_IStream]

    def Clone(self):
        raise COMException("Not today", scode=winerror.E_UNEXPECTED)

    def Commit(self, flags):
        # 049870.python.errorSemantics.line31.comment Testing unicode: 1F600   '😀'; GRINNING FACE
        # 049871.python.errorSemantics.line32.comment Use the 'name' just for fun!
        if flags == 0:
            # 049872.python.errorSemantics.line34.comment A non com-specific exception.
            raise Exception("\N{GRINNING FACE}")
        # 049873.python.errorSemantics.line36.comment An explicit com_error, which is a bit of an edge-case, but might happen if
        # 049874.python.errorSemantics.line37.comment a COM server itself calls another COM object and it fails.
        excepinfo = (
            winerror.E_UNEXPECTED,
            "source",
            "\N{GRINNING FACE}",
            "helpfile",
            1,
            winerror.E_FAIL,
        )
        raise pythoncom.com_error(winerror.E_UNEXPECTED, "desc", excepinfo, None)


def test():
    # 049875.python.errorSemantics.line50.comment Call via a native interface.
    com_server = wrap(TestServer(), pythoncom.IID_IStream)
    try:
        com_server.Clone()
        raise AssertionError("Expecting this call to fail!")
    except pythoncom.com_error as com_exc:
        assert com_exc.hresult == winerror.E_UNEXPECTED, (
            "Calling the object natively did not yield the correct scode",
            str(com_exc),
        )
        exc = com_exc.excepinfo
        assert exc and exc[-1] == winerror.E_UNEXPECTED, (
            "The scode element of the exception tuple did not yield the correct scode",
            str(com_exc),
        )
        assert exc[2] == "Not today", (
            "The description in the exception tuple did not yield the correct string",
            str(com_exc),
        )
    cap = CaptureWriter()
    try:
        cap.capture()
        try:
            com_server.Commit(0)
        finally:
            cap.release()
        raise AssertionError("Expecting this call to fail!")
    except pythoncom.com_error as com_exc:
        assert com_exc.hresult == winerror.E_FAIL, (
            "The hresult was not E_FAIL for an internal error",
            str(com_exc),
        )
        assert com_exc.excepinfo[1] == "Python COM Server Internal Error", (
            "The description in the exception tuple did not yield the correct string",
            str(com_exc),
        )
    # 049876.python.errorSemantics.line86.comment Check we saw a traceback in stderr
    assert cap.get_captured().find("Traceback") >= 0, (
        f"Could not find a traceback in stderr: {cap.get_captured()!r}"
    )

    # 049877.python.errorSemantics.line91.comment Now do it all again, but using IDispatch
    com_server = Dispatch(wrap(TestServer()))
    try:
        com_server.Clone()
        raise AssertionError("Expecting this call to fail!")
    except pythoncom.com_error as com_exc:
        assert com_exc.hresult == winerror.DISP_E_EXCEPTION, (
            "Calling the object via IDispatch did not yield the correct scode",
            str(com_exc),
        )
        exc = com_exc.excepinfo
        assert exc and exc[-1] == winerror.E_UNEXPECTED, (
            "The scode element of the exception tuple did not yield the correct scode",
            str(com_exc),
        )
        assert exc[2] == "Not today", (
            "The description in the exception tuple did not yield the correct string",
            str(com_exc),
        )

    cap.clear()
    try:
        cap.capture()
        try:
            com_server.Commit(0)
        finally:
            cap.release()
        raise AssertionError("Expecting this call to fail!")
    except pythoncom.com_error as com_exc:
        assert com_exc.hresult == winerror.DISP_E_EXCEPTION, (
            "Calling the object via IDispatch did not yield the correct scode",
            str(com_exc),
        )
        exc = com_exc.excepinfo
        assert exc and exc[-1] == winerror.E_FAIL, (
            "The scode element of the exception tuple did not yield the correct scode",
            str(com_exc),
        )
        assert exc[1] == "Python COM Server Internal Error", (
            "The description in the exception tuple did not yield the correct string",
            str(com_exc),
        )
    # 049878.python.errorSemantics.line133.comment Check we saw a traceback in stderr
    assert cap.get_captured().find("Traceback") >= 0, (
        f"Could not find a traceback in stderr: {cap.get_captured()!r}"
    )

    # 049879.python.errorSemantics.line138.comment And an explicit com_error
    cap.clear()
    try:
        cap.capture()
        try:
            com_server.Commit(1)
        finally:
            cap.release()
        raise AssertionError("Expecting this call to fail!")
    except pythoncom.com_error as com_exc:
        assert com_exc.hresult == winerror.DISP_E_EXCEPTION, (
            "Calling the object via IDispatch did not yield the correct scode",
            str(com_exc),
        )
        exc = com_exc.excepinfo
        assert exc and exc[-1] == winerror.E_FAIL, (
            "The scode element of the exception tuple did not yield the correct scode",
            str(com_exc),
        )
        assert exc[1] == "source", (
            "The source in the exception tuple did not yield the correct string",
            str(com_exc),
        )
        assert exc[2] == "\U0001f600", (
            "The description in the exception tuple did not yield the correct string",
            str(com_exc),
        )
        assert exc[3] == "helpfile", (
            "The helpfile in the exception tuple did not yield the correct string",
            str(com_exc),
        )
        assert exc[4] == 1, (
            "The help context in the exception tuple did not yield the correct string",
            str(com_exc),
        )


try:
    import logging
except ImportError:
    logging = None
if logging is not None:
    import win32com

    class TestLogHandler(logging.Handler):
        def __init__(self):
            self.reset()
            logging.Handler.__init__(self)

        def reset(self):
            self.num_emits = 0
            self.last_record = None

        def emit(self, record):
            self.num_emits += 1
            self.last_record = self.format(record)
            return
            print("--- record start")
            print(self.last_record)
            print("--- record end")

    def testLogger():
        assert not hasattr(win32com, "logger")
        handler = TestLogHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        log = logging.getLogger("win32com_test")
        log.addHandler(handler)
        win32com.logger = log
        # 049880.python.errorSemantics.line207.comment Now throw some exceptions!
        # 049881.python.errorSemantics.line208.comment Native interfaces
        com_server = wrap(TestServer(), pythoncom.IID_IStream)
        try:
            com_server.Commit(0)
            raise AssertionError("should have failed")
        except pythoncom.error as exc:
            # 049882.python.errorSemantics.line214.comment `excepinfo` is a tuple with elt 2 being the traceback we captured.
            message = exc.excepinfo[2]
            assert message.endswith("Exception: \U0001f600\n")
        assert handler.num_emits == 1, handler.num_emits
        assert handler.last_record.startswith(
            "pythoncom error: Unexpected exception in gateway method 'Commit'"
        )
        handler.reset()

        # 049883.python.errorSemantics.line223.comment IDispatch
        com_server = Dispatch(wrap(TestServer()))
        try:
            com_server.Commit(0)
            raise AssertionError("should have failed")
        except pythoncom.error as exc:
            # 049884.python.errorSemantics.line229.comment `excepinfo` is a tuple with elt 2 being the traceback we captured.
            message = exc.excepinfo[2]
            assert message.endswith("Exception: \U0001f600\n")
        assert handler.num_emits == 1, handler.num_emits
        handler.reset()


if __name__ == "__main__":
    test()
    if logging is not None:
        testLogger()
    from win32com.test.util import CheckClean

    CheckClean()
    print("error semantic tests worked")
