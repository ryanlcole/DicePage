# 036868.python.progressbar.line1.comment
# 036869.python.progressbar.line2.comment Progress bar control example
# 036870.python.progressbar.line3.comment
# 036871.python.progressbar.line4.comment PyCProgressCtrl encapsulates the MFC CProgressCtrl class.  To use it,
# 036872.python.progressbar.line5.comment you:
# 036873.python.progressbar.line6.comment
# 036874.python.progressbar.line7.comment - Create the control with win32ui.CreateProgressCtrl()
# 036875.python.progressbar.line8.comment - Create the control window with PyCProgressCtrl.CreateWindow()
# 036876.python.progressbar.line9.comment - Initialize the range if you want it to be other than (0, 100) using
# 036877.python.progressbar.line10.comment PyCProgressCtrl.SetRange()
# 036878.python.progressbar.line11.comment - Either:
# 036879.python.progressbar.line12.comment - Set the step size with PyCProgressCtrl.SetStep(), and
# 036880.python.progressbar.line13.comment - Increment using PyCProgressCtrl.StepIt()
# 036881.python.progressbar.line14.comment or:
# 036882.python.progressbar.line15.comment - Set the amount completed using PyCProgressCtrl.SetPos()
# 036883.python.progressbar.line16.comment
# 036884.python.progressbar.line17.comment Example and progress bar code courtesy of KDL Technologies, Ltd., Hong Kong SAR, China.
# 036885.python.progressbar.line18.comment

import win32con
import win32ui
from pywin.mfc import dialog


def MakeDlgTemplate():
    style = (
        win32con.DS_MODALFRAME
        | win32con.WS_POPUP
        | win32con.WS_VISIBLE
        | win32con.WS_CAPTION
        | win32con.WS_SYSMENU
        | win32con.DS_SETFONT
    )
    cs = win32con.WS_CHILD | win32con.WS_VISIBLE

    w = 215
    h = 36

    dlg = [
        [
            "Progress bar control example",
            (0, 0, w, h),
            style,
            None,
            (8, "MS Sans Serif"),
        ],
    ]

    s = win32con.WS_TABSTOP | cs

    dlg.append(
        [
            128,
            "Tick",
            win32con.IDOK,
            (10, h - 18, 50, 14),
            s | win32con.BS_DEFPUSHBUTTON,
        ]
    )

    dlg.append(
        [
            128,
            "Cancel",
            win32con.IDCANCEL,
            (w - 60, h - 18, 50, 14),
            s | win32con.BS_PUSHBUTTON,
        ]
    )

    return dlg


class TestDialog(dialog.Dialog):
    def OnInitDialog(self):
        rc = dialog.Dialog.OnInitDialog(self)
        self.pbar = win32ui.CreateProgressCtrl()
        self.pbar.CreateWindow(
            win32con.WS_CHILD | win32con.WS_VISIBLE, (10, 10, 310, 24), self, 1001
        )
        # 036886.python.progressbar.line81.comment self.pbar.SetStep (5)
        self.progress = 0
        self.pincr = 5
        return rc

    def OnOK(self):
        # 036887.python.progressbar.line87.comment NB: StepIt wraps at the end if you increment past the upper limit!
        # 036888.python.progressbar.line88.comment self.pbar.StepIt()
        self.progress += self.pincr
        if self.progress > 100:
            self.progress = 100
        if self.progress <= 100:
            self.pbar.SetPos(self.progress)


def demo(modal=0):
    d = TestDialog(MakeDlgTemplate())
    if modal:
        d.DoModal()
    else:
        d.CreateWindow()


if __name__ == "__main__":
    demo(1)
