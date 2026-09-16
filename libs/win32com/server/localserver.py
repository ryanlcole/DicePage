# 049633.python.localserver.line1.comment LocalServer .EXE support for Python.
# 049634.python.localserver.line2.comment
# 049635.python.localserver.line3.comment This is designed to be used as a _script_ file by pythonw.exe
# 049636.python.localserver.line4.comment
# 049637.python.localserver.line5.comment In some cases, you could also use Python.exe, which will create
# 049638.python.localserver.line6.comment a console window useful for debugging.
# 049639.python.localserver.line7.comment
# 049640.python.localserver.line8.comment NOTE: When NOT running in any sort of debugging mode,
# 049641.python.localserver.line9.comment 'print' statements may fail, as sys.stdout is not valid!!!

# 049642.python.localserver.line11.comment
# 049643.python.localserver.line12.comment Usage:
# 049644.python.localserver.line13.comment wpython.exe LocalServer.py clsid [, clsid]
import sys

sys.coinit_flags = 2
import pythoncom
import win32api
from win32com.server import factory

usage = """\
Invalid command line arguments

This program provides LocalServer COM support
for Python COM objects.

It is typically run automatically by COM, passing as arguments
The ProgID or CLSID of the Python Server(s) to be hosted
"""


def serve(clsids):
    infos = factory.RegisterClassFactories(clsids)

    pythoncom.EnableQuitMessage(win32api.GetCurrentThreadId())
    pythoncom.CoResumeClassObjects()

    pythoncom.PumpMessages()

    factory.RevokeClassFactories(infos)

    pythoncom.CoUninitialize()


def main():
    if len(sys.argv) == 1:
        win32api.MessageBox(0, usage, "Python COM Server")
        sys.exit(1)
    serve(sys.argv[1:])


if __name__ == "__main__":
    main()
