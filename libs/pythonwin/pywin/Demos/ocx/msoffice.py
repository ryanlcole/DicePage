# 036790.python.msoffice.line1.comment This demo uses some of the Microsoft Office components.
# 036791.python.msoffice.line2.comment
# 036792.python.msoffice.line3.comment It was taken from an MSDN article showing how to embed excel.
# 036793.python.msoffice.line4.comment It is not comlpete yet, but it _does_ show an Excel spreadsheet in a frame!
# 036794.python.msoffice.line5.comment

import win32con
import win32ui
import win32uiole
from pywin.mfc import activex, docview, object, window
from win32com.client import gencache


class OleClientItem(object.CmdTarget):
    def __init__(self, doc):
        object.CmdTarget.__init__(self, win32uiole.CreateOleClientItem(doc))

    def OnGetItemPosition(self):
        # 036795.python.msoffice.line19.comment For now return a hard-coded rect.
        return (10, 10, 210, 210)

    def OnActivate(self):
        # 036796.python.msoffice.line23.comment Allow only one inplace activate item per frame
        view = self.GetActiveView()
        item = self.GetDocument().GetInPlaceActiveItem(view)
        if item is not None and item._obj_ != self._obj_:
            item.Close()
        self._obj_.OnActivate()

    def OnChange(self, oleNotification, dwParam):
        self._obj_.OnChange(oleNotification, dwParam)
        self.GetDocument().UpdateAllViews(None)

    def OnChangeItemPosition(self, rect):
        # 036797.python.msoffice.line35.comment During in-place activation CEmbed_ExcelCntrItem::OnChangeItemPosition
        # 036798.python.msoffice.line36.comment is called by the server to change the position of the in-place
        # 036799.python.msoffice.line37.comment window.  Usually, this is a result of the data in the server
        # 036800.python.msoffice.line38.comment document changing such that the extent has changed or as a result
        # 036801.python.msoffice.line39.comment of in-place resizing.
        # 036802.python.msoffice.line40.comment
        # 036803.python.msoffice.line41.comment The default here is to call the base class, which will call
        # 036804.python.msoffice.line42.comment COleClientItem::SetItemRects to move the item
        # 036805.python.msoffice.line43.comment to the new position.
        if not self._obj_.OnChangeItemPosition(self, rect):
            return 0

        # 036806.python.msoffice.line47.comment TODO: update any cache you may have of the item's rectangle/extent
        return 1


class OleDocument(object.CmdTarget):
    def __init__(self, template):
        object.CmdTarget.__init__(self, win32uiole.CreateOleDocument(template))
        self.EnableCompoundFile()


class ExcelView(docview.ScrollView):
    def OnInitialUpdate(self):
        self.HookMessage(self.OnSetFocus, win32con.WM_SETFOCUS)
        self.HookMessage(self.OnSize, win32con.WM_SIZE)

        self.SetScrollSizes(win32con.MM_TEXT, (100, 100))
        rc = self._obj_.OnInitialUpdate()
        self.EmbedExcel()
        return rc

    def EmbedExcel(self):
        doc = self.GetDocument()
        self.clientItem = OleClientItem(doc)
        self.clientItem.CreateNewItem("Excel.Sheet")
        self.clientItem.DoVerb(-1, self)
        doc.UpdateAllViews(None)

    def OnDraw(self, dc):
        doc = self.GetDocument()
        pos = doc.GetStartPosition()
        clientItem, pos = doc.GetNextItem(pos)
        clientItem.Draw(dc, (10, 10, 210, 210))

    # 036807.python.msoffice.line80.comment Special handling of OnSetFocus and OnSize are required for a container
    # 036808.python.msoffice.line81.comment when an object is being edited in-place.
    def OnSetFocus(self, msg):
        item = self.GetDocument().GetInPlaceActiveItem(self)
        if (
            item is not None
            and item.GetItemState() == win32uiole.COleClientItem_activeUIState
        ):
            wnd = item.GetInPlaceWindow()
            if wnd is not None:
                wnd.SetFocus()
            return 0  # Don't get the base version called.
        return 1  # Call the base version.

    def OnSize(self, params):
        item = self.GetDocument().GetInPlaceActiveItem(self)
        if item is not None:
            item.SetItemRects()
        return 1  # do call the base!


class OleTemplate(docview.DocTemplate):
    def __init__(
        self, resourceId=None, MakeDocument=None, MakeFrame=None, MakeView=None
    ):
        if MakeDocument is None:
            MakeDocument = OleDocument
        if MakeView is None:
            MakeView = ExcelView
        docview.DocTemplate.__init__(
            self, resourceId, MakeDocument, MakeFrame, MakeView
        )


class WordFrame(window.MDIChildWnd):
    def __init__(self, doc=None):
        self._obj_ = win32ui.CreateMDIChild()
        self._obj_.AttachObject(self)
        # 036812.python.msoffice.line118.comment Don't call base class doc/view version...

    def Create(self, title, rect=None, parent=None):
        WordModule = gencache.EnsureModule(
            "{00020905-0000-0000-C000-000000000046}", 1033, 8, 0
        )
        if WordModule is None:
            raise ImportError(
                "Microsoft Word version 8 does not appear to be installed."
            )

        # 036813.python.msoffice.line129.comment WordModule.Word doesn't exist in WordModule, WordModule.Words does, but CreateControl still fails
        class MyWordControl(activex.Control, WordModule.Word): ...

        style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_OVERLAPPEDWINDOW
        self._obj_.CreateWindow(None, title, style, rect, parent)

        rect = self.GetClientRect()
        rect = (0, 0, rect[2] - rect[0], rect[3] - rect[1])
        self.ocx = MyWordControl()
        self.ocx.CreateControl(
            "Microsoft Word", win32con.WS_VISIBLE | win32con.WS_CHILD, rect, self, 20000
        )


def Demo():
    import sys

    import win32api

    docName = None
    if len(sys.argv) > 1:
        docName = win32api.GetFullPathName(sys.argv[1])
    OleTemplate().OpenDocumentFile(docName)

    # 036814.python.msoffice.line153.comment ActiveX not currently working
    # 036815.python.msoffice.line154.comment f = WordFrame(docName)
    # 036816.python.msoffice.line155.comment f.Create("Microsoft Office")


if __name__ == "__main__":
    Demo()
