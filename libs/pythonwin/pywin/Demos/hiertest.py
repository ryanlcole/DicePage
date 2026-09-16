import os

import commctrl
import win32ui
from pywin.mfc import docview, window
from pywin.tools import hierlist


# 036761.python.hiertest.line9.comment directory listbox
# 036762.python.hiertest.line10.comment This has obvious limitations - doesn't track subdirs, etc.  Demonstrates
# 036763.python.hiertest.line11.comment simple use of Python code for querying the tree as needed.
# 036764.python.hiertest.line12.comment Only use strings, and lists of strings (from curdir())
class DirHierList(hierlist.HierList):
    def __init__(self, root, listBoxID=win32ui.IDC_LIST1):
        hierlist.HierList.__init__(self, root, win32ui.IDB_HIERFOLDERS, listBoxID)

    def GetText(self, item):
        return os.path.basename(item)

    def GetSubList(self, item):
        if os.path.isdir(item):
            ret = [os.path.join(item, fname) for fname in os.listdir(item)]
        else:
            ret = None
        return ret

    # 036765.python.hiertest.line27.comment if the item is a dir, it is expandable.
    def IsExpandable(self, item):
        return os.path.isdir(item)

    def GetSelectedBitmapColumn(self, item):
        return self.GetBitmapColumn(item) + 6  # Use different color for selection


class TestDocument(docview.Document):
    def __init__(self, template):
        docview.Document.__init__(self, template)
        self.hierlist = hierlist.HierListWithItems(
            HLIFileDir("\\"), win32ui.IDB_HIERFOLDERS, win32ui.AFX_IDW_PANE_FIRST
        )


class HierListView(docview.TreeView):
    def OnInitialUpdate(self):
        rc = self._obj_.OnInitialUpdate()
        self.hierList = self.GetDocument().hierlist
        self.hierList.HierInit(self.GetParent())
        self.hierList.SetStyle(
            commctrl.TVS_HASLINES | commctrl.TVS_LINESATROOT | commctrl.TVS_HASBUTTONS
        )
        return rc


class HierListFrame(window.MDIChildWnd):
    pass


def GetTestRoot():
    tree1 = ("Tree 1", [("Item 1", "Item 1 data"), "Item 2", 3])
    tree2 = ("Tree 2", [("Item 2.1", "Item 2 data"), "Item 2.2", 2.3])
    return ("Root", [tree1, tree2, "Item 3"])


def demoboth():
    template = docview.DocTemplate(
        win32ui.IDR_PYTHONTYPE, TestDocument, HierListFrame, HierListView
    )
    template.OpenDocumentFile(None).SetTitle("Hierlist demo")

    demomodeless()


def demomodeless():
    testList2 = DirHierList("\\")
    dlg = hierlist.HierDialog("hier list test", testList2)
    dlg.CreateWindow()


def demodlg():
    testList2 = DirHierList("\\")
    dlg = hierlist.HierDialog("hier list test", testList2)
    dlg.DoModal()


def demo():
    template = docview.DocTemplate(
        win32ui.IDR_PYTHONTYPE, TestDocument, HierListFrame, HierListView
    )
    template.OpenDocumentFile(None).SetTitle("Hierlist demo")


# 036767.python.hiertest.line92.comment
# 036768.python.hiertest.line93.comment Demo/Test for HierList items.
# 036769.python.hiertest.line94.comment
# 036770.python.hiertest.line95.comment Easy to make a better directory program.
# 036771.python.hiertest.line96.comment
class HLIFileDir(hierlist.HierListItem):
    def __init__(self, filename):
        self.filename = filename
        hierlist.HierListItem.__init__(self)

    def GetText(self):
        try:
            return "%-20s %d bytes" % (
                os.path.basename(self.filename),
                os.stat(self.filename)[6],
            )
        except OSError as details:
            return "%-20s - %s" % (self.filename, details[1])

    def IsExpandable(self):
        return os.path.isdir(self.filename)

    def GetSubList(self):
        ret = []
        for newname in os.listdir(self.filename):
            if newname not in (".", ".."):
                ret.append(HLIFileDir(os.path.join(self.filename, newname)))
        return ret


def demohli():
    template = docview.DocTemplate(
        win32ui.IDR_PYTHONTYPE,
        TestDocument,
        hierlist.HierListFrame,
        hierlist.HierListView,
    )
    template.OpenDocumentFile(None).SetTitle("Hierlist demo")


if __name__ == "__main__":
    import demoutils

    if demoutils.HaveGoodGUI():
        demoboth()
    else:
        demodlg()
