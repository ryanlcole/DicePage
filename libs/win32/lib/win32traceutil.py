# 047784.python.win32traceutil.line1.comment This is a helper for the win32trace module

# 047785.python.win32traceutil.line3.comment If imported from a normal Python program, it sets up sys.stdout and sys.stderr
# 047786.python.win32traceutil.line4.comment so output goes to the collector.

# 047787.python.win32traceutil.line6.comment If run from the command line, it creates a collector loop.

# 047788.python.win32traceutil.line8.comment Eg:
# 047789.python.win32traceutil.line9.comment C:>start win32traceutil.py (or python.exe win32traceutil.py)
# 047790.python.win32traceutil.line10.comment will start a process with a (pretty much) blank screen.
# 047791.python.win32traceutil.line11.comment
# 047792.python.win32traceutil.line12.comment then, switch to a DOS prompt, and type:
# 047793.python.win32traceutil.line13.comment C:>python.exe
# 047794.python.win32traceutil.line14.comment Python X.X.X (#0, Apr 13 1999, ...
# 047795.python.win32traceutil.line15.comment >>> import win32traceutil
# 047796.python.win32traceutil.line16.comment Redirecting output to win32trace remote collector
# 047797.python.win32traceutil.line17.comment >>> print("Hello")
# 047798.python.win32traceutil.line18.comment >>>
# 047799.python.win32traceutil.line19.comment And the output will appear in the first collector process.

# 047800.python.win32traceutil.line21.comment Note - the client or the collector can be started first.
# 047801.python.win32traceutil.line22.comment There is a 0x20000 byte buffer.  If this gets full, it is reset, and new
# 047802.python.win32traceutil.line23.comment output appended from the start.

import win32trace


def RunAsCollector():
    import sys

    try:
        import win32api

        win32api.SetConsoleTitle("Python Trace Collector")
    except:
        pass  # Oh well!
    win32trace.InitRead()
    print("Collecting Python Trace Output...")
    try:
        while 1:
            # 047804.python.win32traceutil.line41.comment a short timeout means ctrl+c works next time we wake...
            sys.stdout.write(win32trace.blockingread(500))
    except KeyboardInterrupt:
        print("Ctrl+C")


def SetupForPrint():
    win32trace.InitWrite()
    try:  # Under certain servers, sys.stdout may be invalid.
        print("Redirecting output to win32trace remote collector")
    except:
        pass
    win32trace.setprint()  # this works in an rexec environment.


if __name__ == "__main__":
    RunAsCollector()
else:
    SetupForPrint()
