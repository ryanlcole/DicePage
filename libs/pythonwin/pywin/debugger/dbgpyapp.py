# 036969.python.dbgpyapp.line1.comment dbgpyapp.py  - Debugger Python application class
# 036970.python.dbgpyapp.line2.comment
import sys

import win32con
import win32ui
from pywin.framework import intpyapp

version = "0.3.0"


class DebuggerPythonApp(intpyapp.InteractivePythonApp):
    def LoadMainFrame(self):
        "Create the main applications frame"
        self.frame = self.CreateMainFrame()
        self.SetMainFrame(self.frame)
        self.frame.LoadFrame(win32ui.IDR_DEBUGGER, win32con.WS_OVERLAPPEDWINDOW)
        self.frame.DragAcceptFiles()  # we can accept these.
        self.frame.ShowWindow(win32con.SW_HIDE)
        self.frame.UpdateWindow()

        # 036972.python.dbgpyapp.line22.comment but we do rehook, hooking the new code objects.
        self.HookCommands()

    def InitInstance(self):
        # 036973.python.dbgpyapp.line26.comment Use a registry path of "Python\Pythonwin Debugger
        win32ui.SetAppName(win32ui.LoadString(win32ui.IDR_DEBUGGER))
        win32ui.SetRegistryKey(f"Python {sys.winver}")
        # 036974.python.dbgpyapp.line29.comment We _need_ the Scintilla color editor.
        # 036975.python.dbgpyapp.line30.comment (and we _always_ get it now :-)

        numMRU = win32ui.GetProfileVal("Settings", "Recent File List Size", 10)
        win32ui.LoadStdProfileSettings(numMRU)

        self.LoadMainFrame()

        # 036976.python.dbgpyapp.line37.comment Display the interactive window if the user wants it.
        from pywin.framework import interact

        interact.CreateInteractiveWindowUserPreference()

        # 036977.python.dbgpyapp.line42.comment Load the modules we use internally.
        self.LoadSystemModules()
        # 036978.python.dbgpyapp.line44.comment Load additional module the user may want.
        self.LoadUserModules()

        # 036979.python.dbgpyapp.line47.comment win32ui.CreateDebuggerThread()
        win32ui.EnableControlContainer()
