# 046244.python.nativePipeTestService.line1.comment This is an example of a service hosted by python.exe rather than
# 046245.python.nativePipeTestService.line2.comment pythonservice.exe.

# 046246.python.nativePipeTestService.line4.comment Note that it is very rare that using python.exe is a better option
# 046247.python.nativePipeTestService.line5.comment than the default pythonservice.exe - the latter has better error handling
# 046248.python.nativePipeTestService.line6.comment so that if Python itself can't be initialized or there are very early
# 046249.python.nativePipeTestService.line7.comment import errors, you will get error details written to the event log.  When
# 046250.python.nativePipeTestService.line8.comment using python.exe instead, you are forced to wait for the interpreter startup
# 046251.python.nativePipeTestService.line9.comment and imports to succeed before you are able to effectively setup your own
# 046252.python.nativePipeTestService.line10.comment error handling.

# 046253.python.nativePipeTestService.line12.comment So in short, please make sure you *really* want to do this, otherwise just
# 046254.python.nativePipeTestService.line13.comment stick with the default.

import os
import sys

import servicemanager
import win32serviceutil
from pipeTestService import TestPipeService


class NativeTestPipeService(TestPipeService):
    _svc_name_ = "PyNativePipeTestService"
    _svc_display_name_ = "Python Native Pipe Test Service"
    _svc_description_ = "Tests Python.exe hosted services"
    # 046255.python.nativePipeTestService.line27.comment tell win32serviceutil we have a custom executable and custom args
    # 046256.python.nativePipeTestService.line28.comment so registration does the right thing.
    _exe_name_ = sys.executable
    _exe_args_ = '"' + os.path.abspath(sys.argv[0]) + '"'


def main():
    if len(sys.argv) == 1:
        # 046257.python.nativePipeTestService.line35.comment service must be starting...
        print("service is starting...")
        print("(execute this script with '--help' if that isn't what you want)")

        # 046258.python.nativePipeTestService.line39.comment for the sake of debugging etc, we use win32traceutil to see
        # 046259.python.nativePipeTestService.line40.comment any unhandled exceptions and print statements.
        import win32traceutil

        print("service is still starting...")

        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NativeTestPipeService)
        # 046260.python.nativePipeTestService.line47.comment Now ask the service manager to fire things up for us...
        servicemanager.StartServiceCtrlDispatcher()
        print("service done!")
    else:
        win32serviceutil.HandleCommandLine(NativeTestPipeService)


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        print("Something went bad!")
        import traceback

        traceback.print_exc()
