import os
import sys
import traceback

import pythoncom
import win32ui
from win32com.axscript.server import axsite
from win32com.server import util

version = "0.0.1"


class MySite(axsite.AXSite):
    def OnScriptError(self, error):
        print("An error occurred in the Script Code")
        exc = error.GetExceptionInfo()
        try:
            text = error.GetSourceLineText()
        except:
            text = "<unknown>"
        context, line, char = error.GetSourcePosition()
        print(
            "Exception: %s (line %d)\n%s\n%s^\n%s"
            % (exc[1], line, text, " " * (char - 1), exc[2])
        )


class ObjectModel:
    _public_methods_ = ["echo", "msgbox"]

    def echo(self, *args):
        print("".join(map(str, args)))

    def msgbox(self, *args):
        msg = "".join(map(str, args))
        win32ui.MessageBox(msg)


def TestEngine():
    model = {"Test": util.wrap(ObjectModel())}
    scriptDir = "."
    site = MySite(model)
    pyEngine = site._AddEngine("Python")
    # 051316.python.testHost4Dbg.line44.comment pyEngine2 = site._AddEngine("Python")
    vbEngine = site._AddEngine("VBScript")
    # 051317.python.testHost4Dbg.line46.comment forthEngine = site._AddEngine("ForthScript")
    try:
        # 051318.python.testHost4Dbg.line48.comment code = open(os.path.join(scriptDir, "debugTest.4ths"),"rb").read()
        # 051319.python.testHost4Dbg.line49.comment forthEngine.AddCode(code)
        code = open(os.path.join(scriptDir, "debugTest.pys"), "rb").read()
        pyEngine.AddCode(code)
        code = open(os.path.join(scriptDir, "debugTest.vbs"), "rb").read()
        vbEngine.AddCode(code)
        # 051320.python.testHost4Dbg.line54.comment code = open(os.path.join(scriptDir, "debugTestFail.pys"),"rb").read()
        # 051321.python.testHost4Dbg.line55.comment pyEngine2.AddCode(code)

        # 051322.python.testHost4Dbg.line57.comment from win32com.axdebug import axdebug
        # 051323.python.testHost4Dbg.line58.comment sessionProvider=pythoncom.CoCreateInstance(axdebug.CLSID_DefaultDebugSessionProvider,None,pythoncom.CLSCTX_ALL, axdebug.IID_IDebugSessionProvider)
        # 051324.python.testHost4Dbg.line59.comment sessionProvider.StartDebugSession(None)

        input("Press enter to continue")
        # 051325.python.testHost4Dbg.line62.comment forthEngine.Start()
        pyEngine.Start()  # Actually run the Python code
        vbEngine.Start()  # Actually run the VB code
    except pythoncom.com_error as details:
        print(f"Script failed: {details[1]} (0x{details[0]:x})")
    # 051328.python.testHost4Dbg.line67.comment Now run the code expected to fail!
    # 051329.python.testHost4Dbg.line68.comment try:
    # 051330.python.testHost4Dbg.line69.comment pyEngine2.Start()  # Actually run the Python code that fails!
    # 051331.python.testHost4Dbg.line70.comment print("Script code worked when it should have failed.")
    # 051332.python.testHost4Dbg.line71.comment except pythoncom.com_error:
    # 051333.python.testHost4Dbg.line72.comment pass

    site._Close()


if __name__ == "__main__":
    try:
        TestEngine()
    except:
        traceback.print_exc()
    sys.exc_type = sys.exc_value = sys.exc_traceback = None
    print(pythoncom._GetInterfaceCount(), "com objects still alive")
