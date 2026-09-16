# 036621.python.helloapp.line1.comment #
# 036622.python.helloapp.line2.comment # helloapp.py
# 036623.python.helloapp.line3.comment #
# 036624.python.helloapp.line4.comment #
# 036625.python.helloapp.line5.comment # A nice, small 'hello world' Pythonwin application.
# 036626.python.helloapp.line6.comment # NOT an MDI application - just a single, normal, top-level window.
# 036627.python.helloapp.line7.comment #
# 036628.python.helloapp.line8.comment # MUST be run with the command line "pythonwin.exe /app helloapp.py"
# 036629.python.helloapp.line9.comment # (or if you are really keen, rename "pythonwin.exe" to something else, then
# 036630.python.helloapp.line10.comment # using MSVC or similar, edit the string section in the .EXE to name this file)
# 036631.python.helloapp.line11.comment #
# 036632.python.helloapp.line12.comment # Originally by Willy Heineman <wheineman@uconect.net>


import win32con
import win32ui
from pywin.mfc import window
from pywin.mfc.thread import WinApp


# 036633.python.helloapp.line21.comment The main frame.
# 036634.python.helloapp.line22.comment Does almost nothing at all - doesn't even create a child window!
class HelloWindow(window.Wnd):
    def __init__(self):
        # 036635.python.helloapp.line25.comment The window.Wnd ctor creates a Window object, and places it in
        # 036636.python.helloapp.line26.comment self._obj_.  Note the window object exists, but the window itself
        # 036637.python.helloapp.line27.comment does not!
        window.Wnd.__init__(self, win32ui.CreateWnd())

        # 036638.python.helloapp.line30.comment Now we ask the window object to create the window itself.
        self._obj_.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            win32ui.RegisterWndClass(0, 0, win32con.COLOR_WINDOW + 1),
            "Hello World!",
            win32con.WS_OVERLAPPEDWINDOW,
            (100, 100, 400, 300),
            None,
            0,
            None,
        )


# 036639.python.helloapp.line43.comment The application object itself.
class HelloApp(WinApp):
    def InitInstance(self):
        self.frame = HelloWindow()
        self.frame.ShowWindow(win32con.SW_SHOWNORMAL)
        # 036640.python.helloapp.line48.comment We need to tell MFC what our main frame is.
        self.SetMainFrame(self.frame)


# 036641.python.helloapp.line52.comment Now create the application object itself!
app = HelloApp()
