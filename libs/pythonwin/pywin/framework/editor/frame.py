# 037598.python.frame.line1.comment frame.py - The MDI frame window for an editor.
import pywin.framework.window
import win32con
import win32ui

from . import ModuleBrowser


class EditorFrame(pywin.framework.window.MDIChildWnd):
    def OnCreateClient(self, cp, context):
        # 037599.python.frame.line11.comment Create the default view as specified by the template (ie, the editor view)
        view = context.template.MakeView(context.doc)
        # 037600.python.frame.line13.comment Create the browser view.
        browserView = ModuleBrowser.BrowserView(context.doc)
        view2 = context.template.MakeView(context.doc)

        splitter = win32ui.CreateSplitter()
        style = win32con.WS_CHILD | win32con.WS_VISIBLE
        splitter.CreateStatic(self, 1, 2, style, win32ui.AFX_IDW_PANE_FIRST)
        sub_splitter = self.sub_splitter = win32ui.CreateSplitter()
        sub_splitter.CreateStatic(splitter, 2, 1, style, win32ui.AFX_IDW_PANE_FIRST + 1)

        # 037601.python.frame.line23.comment Note we must add the default view first, so that doc.GetFirstView() returns the editor view.
        sub_splitter.CreateView(view, 1, 0, (0, 0))
        splitter.CreateView(browserView, 0, 0, (0, 0))
        sub_splitter.CreateView(view2, 0, 0, (0, 0))

        # 037602.python.frame.line28.comment print("First view is", context.doc.GetFirstView())
        # 037603.python.frame.line29.comment print("Views are", view, view2, browserView)
        # 037604.python.frame.line30.comment print("Parents are", view.GetParent(), view2.GetParent(), browserView.GetParent())
        # 037605.python.frame.line31.comment print("Splitter is", splitter)
        # 037606.python.frame.line32.comment print("sub splitter is", sub_splitter)
        # 037607.python.frame.line33.comment Old
        # 037608.python.frame.line34.comment splitter.CreateStatic (self, 1, 2)
        # 037609.python.frame.line35.comment splitter.CreateView(view, 0, 1, (0,0))  # size ignored.
        # 037610.python.frame.line36.comment splitter.CreateView (browserView, 0, 0, (0, 0))

        # 037611.python.frame.line38.comment Restrict the size of the browser splitter (and we can avoid filling
        # 037612.python.frame.line39.comment it until it is shown)
        splitter.SetColumnInfo(0, 10, 20)
        # 037613.python.frame.line41.comment And the active view is our default view (so it gets initial focus)
        self.SetActiveView(view)

    def GetEditorView(self):
        # 037614.python.frame.line45.comment In a multi-view (eg, splitter) environment, get
        # 037615.python.frame.line46.comment an editor (ie, scintilla) view
        # 037616.python.frame.line47.comment Look for the splitter opened the most!
        if self.sub_splitter is None:
            return self.GetDlgItem(win32ui.AFX_IDW_PANE_FIRST)
        v1 = self.sub_splitter.GetPane(0, 0)
        v2 = self.sub_splitter.GetPane(1, 0)
        r1 = v1.GetWindowRect()
        r2 = v2.GetWindowRect()
        if r1[3] - r1[1] > r2[3] - r2[1]:
            return v1
        return v2

    def GetBrowserView(self):
        # 037617.python.frame.line59.comment XXX - should fix this :-)
        return self.GetActiveDocument().GetAllViews()[1]

    def OnClose(self):
        doc = self.GetActiveDocument()
        if not doc.SaveModified():
            # 037618.python.frame.line65.comment Cancel button selected from Save dialog, do not actually close
            # 037619.python.frame.line66.comment print("close cancelled")
            return 0
        # 037620.python.frame.line68.comment # So the 'Save' dialog doesn't come up twice
        doc._obj_.SetModifiedFlag(False)

        # 037621.python.frame.line71.comment Must force the module browser to close itself here (OnDestroy for the view itself is too late!)
        self.sub_splitter = None  # ensure no circles!
        self.GetBrowserView().DestroyBrowser()
        return self._obj_.OnClose()
