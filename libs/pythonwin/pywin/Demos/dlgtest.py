# 036675.python.dlgtest.line1.comment A Demo of Pythonwin's Dialog and Property Page support.

# 036676.python.dlgtest.line3.comment ##################
# 036677.python.dlgtest.line4.comment
# 036678.python.dlgtest.line5.comment First demo - use the built-in to Pythonwin "Tab Stop" dialog, but
# 036679.python.dlgtest.line6.comment customise it heavily.
# 036680.python.dlgtest.line7.comment
# 036681.python.dlgtest.line8.comment ID's for the tabstop dialog - out test.
# 036682.python.dlgtest.line9.comment
import win32con
import win32ui
from pywin.mfc import dialog
from win32con import IDCANCEL
from win32ui import IDC_EDIT_TABS, IDC_PROMPT_TABS, IDD_SET_TABSTOPS


class TestDialog(dialog.Dialog):
    def __init__(self, modal=1):
        dialog.Dialog.__init__(self, IDD_SET_TABSTOPS)
        self.counter = 0
        if modal:
            self.DoModal()
        else:
            self.CreateWindow()

    def OnInitDialog(self):
        # 036683.python.dlgtest.line27.comment Set the caption of the dialog itself.
        self.SetWindowText("Used to be Tab Stops!")
        # 036684.python.dlgtest.line29.comment Get a child control, remember it, and change its text.
        self.edit = self.GetDlgItem(IDC_EDIT_TABS)  # the text box.
        self.edit.SetWindowText("Test")
        # 036686.python.dlgtest.line32.comment Hook a Windows message for the dialog.
        self.edit.HookMessage(self.KillFocus, win32con.WM_KILLFOCUS)
        # 036687.python.dlgtest.line34.comment Get the prompt control, and change its next.
        prompt = self.GetDlgItem(IDC_PROMPT_TABS)  # the prompt box.
        prompt.SetWindowText("Prompt")
        # 036689.python.dlgtest.line37.comment And the same for the button..
        cancel = self.GetDlgItem(IDCANCEL)  # the cancel button
        cancel.SetWindowText("&Kill me")

        # 036691.python.dlgtest.line41.comment And just for demonstration purposes, we hook the notify message for the dialog.
        # 036692.python.dlgtest.line42.comment This allows us to be notified when the Edit Control text changes.
        self.HookCommand(self.OnNotify, IDC_EDIT_TABS)

    def OnNotify(self, controlid, code):
        if code == win32con.EN_CHANGE:
            print("Edit text changed!")
        return 1  # I handled this, so no need to call defaults!

    # 036694.python.dlgtest.line50.comment kill focus for the edit box.
    # 036695.python.dlgtest.line51.comment Simply increment the value in the text box.
    def KillFocus(self, msg):
        self.counter += 1
        if self.edit is not None:
            self.edit.SetWindowText(str(self.counter))

    # 036696.python.dlgtest.line57.comment Called when the dialog box is terminating...
    def OnDestroy(self, msg):
        del self.edit
        del self.counter


# 036697.python.dlgtest.line63.comment A very simply Property Sheet.
# 036698.python.dlgtest.line64.comment We only make a new class for demonstration purposes.
class TestSheet(dialog.PropertySheet):
    def __init__(self, title):
        dialog.PropertySheet.__init__(self, title)
        self.HookMessage(self.OnActivate, win32con.WM_ACTIVATE)

    def OnActivate(self, msg):
        pass


# 036699.python.dlgtest.line74.comment A very simply Property Page, which will be "owned" by the above
# 036700.python.dlgtest.line75.comment Property Sheet.
# 036701.python.dlgtest.line76.comment We create a new class, just so we can hook a control notification.
class TestPage(dialog.PropertyPage):
    def OnInitDialog(self):
        # 036702.python.dlgtest.line79.comment We use the HookNotify function to allow Python to respond to
        # 036703.python.dlgtest.line80.comment Windows WM_NOTIFY messages.
        # 036704.python.dlgtest.line81.comment In this case, we are interested in BN_CLICKED messages.
        self.HookNotify(self.OnNotify, win32con.BN_CLICKED)

    def OnNotify(self, std, extra):
        print("OnNotify", std, extra)


# 036705.python.dlgtest.line88.comment Some code that actually uses these objects.
def demo(modal=0):
    TestDialog(modal)

    # 036706.python.dlgtest.line92.comment property sheet/page demo
    ps = win32ui.CreatePropertySheet("Property Sheet/Page Demo")
    # 036707.python.dlgtest.line94.comment Create a completely standard PropertyPage.
    page1 = win32ui.CreatePropertyPage(win32ui.IDD_PROPDEMO1)
    # 036708.python.dlgtest.line96.comment Create our custom property page.
    page2 = TestPage(win32ui.IDD_PROPDEMO2)
    ps.AddPage(page1)
    ps.AddPage(page2)
    if modal:
        ps.DoModal()
    else:
        style = (
            win32con.WS_SYSMENU
            | win32con.WS_POPUP
            | win32con.WS_CAPTION
            | win32con.DS_MODALFRAME
            | win32con.WS_VISIBLE
        )
        styleex = win32con.WS_EX_DLGMODALFRAME | win32con.WS_EX_PALETTEWINDOW
        ps.CreateWindow(win32ui.GetMainFrame(), style, styleex)


def test(modal=1):
    # 036709.python.dlgtest.line115.comment dlg=dialog.Dialog(1010)
    # 036710.python.dlgtest.line116.comment dlg.CreateWindow()
    # 036711.python.dlgtest.line117.comment dlg.EndDialog(0)
    # 036712.python.dlgtest.line118.comment del dlg
    # 036713.python.dlgtest.line119.comment return
    # 036714.python.dlgtest.line120.comment property sheet/page demo
    ps = TestSheet("Property Sheet/Page Demo")
    page1 = win32ui.CreatePropertyPage(win32ui.IDD_PROPDEMO1)
    page2 = win32ui.CreatePropertyPage(win32ui.IDD_PROPDEMO2)
    ps.AddPage(page1)
    ps.AddPage(page2)
    del page1
    del page2
    if modal:
        ps.DoModal()
    else:
        ps.CreateWindow(win32ui.GetMainFrame())
    return ps


def d():
    dlg = win32ui.CreateDialog(win32ui.IDD_DEBUGGER)
    dlg.datalist.append((win32ui.IDC_DBG_RADIOSTACK, "radio"))
    print("data list is ", dlg.datalist)
    dlg.data["radio"] = 1
    dlg.DoModal()
    print(dlg.data["radio"])


if __name__ == "__main__":
    demo(1)
