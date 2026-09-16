# 036610.python.dojobapp.line1.comment dojobapp - do a job, show the result in a dialog, and exit.
# 036611.python.dojobapp.line2.comment
# 036612.python.dojobapp.line3.comment Very simple - faily minimal dialog based app.
# 036613.python.dojobapp.line4.comment
# 036614.python.dojobapp.line5.comment This should be run using the command line:
# 036615.python.dojobapp.line6.comment pythonwin /app demos\dojobapp.py


import win32con
import win32ui
from pywin.framework import dlgappcore


class DoJobAppDialog(dlgappcore.AppDialog):
    softspace = 1

    def __init__(self, appName=""):
        self.appName = appName
        dlgappcore.AppDialog.__init__(self, win32ui.IDD_GENERAL_STATUS)

    def PreDoModal(self):
        pass

    def ProcessArgs(self, args):
        pass

    def OnInitDialog(self):
        self.SetWindowText(self.appName)
        butCancel = self.GetDlgItem(win32con.IDCANCEL)
        butCancel.ShowWindow(win32con.SW_HIDE)
        p1 = self.GetDlgItem(win32ui.IDC_PROMPT1)
        p2 = self.GetDlgItem(win32ui.IDC_PROMPT2)

        # 036616.python.dojobapp.line34.comment Do something here!

        p1.SetWindowText("Hello there")
        p2.SetWindowText("from the demo")

    def OnDestroy(self, msg):
        pass


# 036617.python.dojobapp.line43.comment def OnOK(self):
# 036618.python.dojobapp.line44.comment pass
# 036619.python.dojobapp.line45.comment def OnCancel(self): default behaviour - cancel == close.
# 036620.python.dojobapp.line46.comment return


class DoJobDialogApp(dlgappcore.DialogApp):
    def CreateDialog(self):
        return DoJobAppDialog("Do Something")


class CopyToDialogApp(DoJobDialogApp):
    def __init__(self):
        DoJobDialogApp.__init__(self)


app = DoJobDialogApp()


def t():
    t = DoJobAppDialog("Copy To")
    t.DoModal()
    return t


if __name__ == "__main__":
    import demoutils

    demoutils.NeedApp()
