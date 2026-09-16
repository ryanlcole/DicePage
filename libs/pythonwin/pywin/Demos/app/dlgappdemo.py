# 036602.python.dlgappdemo.line1.comment dlgappdemo - a demo of a dialog application.
# 036603.python.dlgappdemo.line2.comment This is a demonstration of both a custom "application" module,
# 036604.python.dlgappdemo.line3.comment and a Python program in a dialog box.
# 036605.python.dlgappdemo.line4.comment
# 036606.python.dlgappdemo.line5.comment NOTE:  You CAN NOT import this module from either PythonWin or Python.
# 036607.python.dlgappdemo.line6.comment This module must be specified on the commandline to PythonWin only.
# 036608.python.dlgappdemo.line7.comment eg, PythonWin /app dlgappdemo.py

import sys

import win32ui
from pywin.framework import dlgappcore


class TestDialogApp(dlgappcore.DialogApp):
    def CreateDialog(self):
        return TestAppDialog()


class TestAppDialog(dlgappcore.AppDialog):
    def __init__(self):
        self.edit = None
        dlgappcore.AppDialog.__init__(self, win32ui.IDD_LARGE_EDIT)

    def OnInitDialog(self):
        self.SetWindowText("Test dialog application")
        self.edit = self.GetDlgItem(win32ui.IDC_EDIT1)
        print("Hello from Python")
        print("args are:", end=" ")
        for arg in sys.argv:
            print(arg)
        return 1

    def PreDoModal(self):
        sys.stdout = sys.stderr = self

    def write(self, str):
        if self.edit:
            self.edit.SetSel(-2)
            # 036609.python.dlgappdemo.line40.comment translate \n to \n\r
            self.edit.ReplaceSel(str.replace("\n", "\r\n"))
        else:
            win32ui.OutputDebug("dlgapp - no edit control! >>\n%s\n<<\n" % str)


app = TestDialogApp()

if __name__ == "__main__":
    import demoutils

    demoutils.NeedApp()
