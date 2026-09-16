# 036929.python.toolbar.line1.comment Demo of ToolBars

# 036930.python.toolbar.line3.comment Shows the toolbar control.
# 036931.python.toolbar.line4.comment Demos how to make custom tooltips, etc.

import commctrl
import win32con
import win32ui
from pywin.mfc import afxres, docview, window


class GenericFrame(window.MDIChildWnd):
    def OnCreateClient(self, cp, context):
        # 036932.python.toolbar.line14.comment handlers for toolbar buttons
        self.HookCommand(self.OnPrevious, 401)
        self.HookCommand(self.OnNext, 402)
        # 036933.python.toolbar.line17.comment It's not necessary for us to hook both of these - the
        # 036934.python.toolbar.line18.comment common controls should fall-back all by themselves.
        # 036935.python.toolbar.line19.comment Indeed, given we hook TTN_NEEDTEXTW, commctrl.TTN_NEEDTEXTA
        # 036936.python.toolbar.line20.comment will not be called.
        self.HookNotify(self.GetTTText, commctrl.TTN_NEEDTEXT)
        self.HookNotify(self.GetTTText, commctrl.TTN_NEEDTEXTW)

        # 036937.python.toolbar.line24.comment parent = win32ui.GetMainFrame()
        parent = self
        style = (
            win32con.WS_CHILD
            | win32con.WS_VISIBLE
            | afxres.CBRS_SIZE_DYNAMIC
            | afxres.CBRS_TOP
            | afxres.CBRS_TOOLTIPS
            | afxres.CBRS_FLYBY
        )

        buttons = (win32ui.ID_APP_ABOUT, win32ui.ID_VIEW_INTERACTIVE)
        bitmap = win32ui.IDB_BROWSER_HIER
        tbid = 0xE840
        self.toolbar = tb = win32ui.CreateToolBar(parent, style, tbid)
        tb.LoadBitmap(bitmap)
        tb.SetButtons(buttons)

        tb.EnableDocking(afxres.CBRS_ALIGN_ANY)
        tb.SetWindowText("Test")
        parent.EnableDocking(afxres.CBRS_ALIGN_ANY)
        parent.DockControlBar(tb)
        parent.LoadBarState("ToolbarTest")
        window.MDIChildWnd.OnCreateClient(self, cp, context)
        return 1

    def OnDestroy(self, msg):
        self.SaveBarState("ToolbarTest")

    def GetTTText(self, std, extra):
        (hwndFrom, idFrom, code) = std
        text, hinst, flags = extra
        if flags & commctrl.TTF_IDISHWND:
            return  # Not handled
        if idFrom == win32ui.ID_APP_ABOUT:
            # 036939.python.toolbar.line59.comment our 'extra' return value needs to be the following
            # 036940.python.toolbar.line60.comment entries from a NMTTDISPINFO[W] struct:
            # 036941.python.toolbar.line61.comment (szText, hinst, uFlags).  None means 'don't change
            # 036942.python.toolbar.line62.comment the value'
            return 0, ("It works!", None, None)
        return None  # not handled.

    def GetMessageString(self, id):
        if id == win32ui.ID_APP_ABOUT:
            return "Dialog Test\nTest"
        else:
            return self._obj_.GetMessageString(id)

    def OnSize(self, params):
        print("OnSize called with ", params)

    def OnNext(self, id, cmd):
        print("OnNext called")

    def OnPrevious(self, id, cmd):
        print("OnPrevious called")


msg = """\
This toolbar was dynamically created.\r
\r
The first item's tooltips is provided by Python code.\r
\r
(Don't close the window with the toolbar in a floating state - it may not re-appear!)\r
"""


def test():
    template = docview.DocTemplate(
        win32ui.IDR_PYTHONTYPE, None, GenericFrame, docview.EditView
    )
    doc = template.OpenDocumentFile(None)
    doc.SetTitle("Toolbar Test")
    view = doc.GetFirstView()
    view.SetWindowText(msg)


if __name__ == "__main__":
    import demoutils

    if demoutils.NeedGoodGUI():
        test()
