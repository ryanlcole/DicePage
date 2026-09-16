# 039037.python.TraceCollector.line1.comment win32traceutil like utility for Pythonwin
import _thread

import win32api
import win32event
import win32trace
from pywin.framework import winout

outputWindow = None


def CollectorThread(stopEvent, file):
    win32trace.InitRead()
    handle = win32trace.GetHandle()
    # 039038.python.TraceCollector.line15.comment Run this thread at a lower priority to the main message-loop (and printing output)
    # 039039.python.TraceCollector.line16.comment thread can keep up
    import win32process

    win32process.SetThreadPriority(
        win32api.GetCurrentThread(), win32process.THREAD_PRIORITY_BELOW_NORMAL
    )

    try:
        while 1:
            rc = win32event.WaitForMultipleObjects(
                (handle, stopEvent), 0, win32event.INFINITE
            )
            if rc == win32event.WAIT_OBJECT_0:
                # 039040.python.TraceCollector.line29.comment About the only char we can't live with is \0!
                file.write(win32trace.read().replace("\0", "<null>"))
            else:
                # 039041.python.TraceCollector.line32.comment Stop event
                break
    finally:
        win32trace.TermRead()
        print("Thread dieing")


class WindowOutput(winout.WindowOutput):
    def __init__(self, *args):
        winout.WindowOutput.__init__(*(self,) + args)
        self.hStopThread = win32event.CreateEvent(None, 0, 0, None)
        _thread.start_new(CollectorThread, (self.hStopThread, self))

    def _StopThread(self):
        win32event.SetEvent(self.hStopThread)
        self.hStopThread = None

    def Close(self):
        self._StopThread()
        winout.WindowOutput.Close(self)
        # 039042.python.TraceCollector.line52.comment def OnViewDestroy(self, frame):
        # 039043.python.TraceCollector.line53.comment return winout.WindowOutput.OnViewDestroy(self, frame)
        # 039044.python.TraceCollector.line54.comment def Create(self, title=None, style = None):
        # 039045.python.TraceCollector.line55.comment rc = winout.WindowOutput.Create(self, title, style)
        # 039046.python.TraceCollector.line56.comment return rc


def MakeOutputWindow():
    # 039047.python.TraceCollector.line60.comment Note that it will not show until the first string written or
    # 039048.python.TraceCollector.line61.comment you pass bShow = 1
    global outputWindow
    if outputWindow is None:
        title = "Python Trace Collector"
        # 039049.python.TraceCollector.line65.comment queueingFlag doesn't matter, as all output will come from new thread
        outputWindow = WindowOutput(title, title)
        # 039050.python.TraceCollector.line67.comment Let people know what this does!
        msg = """\
# This window will display output from any programs that import win32traceutil
# win32com servers registered with '--debug' are in this category.
"""
        outputWindow.write(msg)
    # 039051.python.TraceCollector.line73.comment force existing window open
    outputWindow.write("")
    return outputWindow


if __name__ == "__main__":
    MakeOutputWindow()
