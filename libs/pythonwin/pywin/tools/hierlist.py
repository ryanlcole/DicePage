# 039094.python.hierlist.line1.comment hierlist
# 039095.python.hierlist.line2.comment
# 039096.python.hierlist.line3.comment IMPORTANT - Please read before using.

# 039097.python.hierlist.line5.comment This module exposes an API for a Hierarchical Tree Control.
# 039098.python.hierlist.line6.comment Previously, a custom tree control was included in Pythonwin which
# 039099.python.hierlist.line7.comment has an API very similar to this.

# 039100.python.hierlist.line9.comment The current control used is the common "Tree Control".  This module exists now
# 039101.python.hierlist.line10.comment to provide an API similar to the old control, but for the new Tree control.

# 039102.python.hierlist.line12.comment If you need to use the Tree Control, you may still find this API a reasonable
# 039103.python.hierlist.line13.comment choice.  However, you should investigate using the tree control directly
# 039104.python.hierlist.line14.comment to provide maximum flexibility (but with extra work).
from __future__ import annotations

import commctrl
import win32api
import win32con
import win32ui
from pywin.mfc import dialog, object
from win32api import RGB


# 039105.python.hierlist.line25.comment helper to get the text of an arbitary item
def GetItemText(item):
    if isinstance(item, (tuple, list)):
        use = item[0]
    else:
        use = item
    if isinstance(use, str):
        return use
    else:
        return repr(item)


class HierDialog(dialog.Dialog):
    def __init__(
        self,
        title,
        hierList,
        bitmapID=win32ui.IDB_HIERFOLDERS,
        dlgID=win32ui.IDD_TREE,
        dll=None,
        childListBoxID=win32ui.IDC_LIST1,
    ):
        dialog.Dialog.__init__(self, dlgID, dll)  # reuse this dialog.
        self.hierList = hierList
        self.dlgID = dlgID
        self.title = title

    # 039107.python.hierlist.line52.comment self.childListBoxID = childListBoxID
    def OnInitDialog(self):
        self.SetWindowText(self.title)
        self.hierList.HierInit(self)
        return dialog.Dialog.OnInitDialog(self)


class HierList(object.Object):
    def __init__(
        self, root, bitmapID=win32ui.IDB_HIERFOLDERS, listBoxId=None, bitmapMask=None
    ):  # used to create object.
        self.listControl = None
        self.bitmapID = bitmapID
        self.root = root
        self.listBoxId = listBoxId
        self.itemHandleMap = {}
        self.filledItemHandlesMap = {}
        self.bitmapMask = bitmapMask

    def __getattr__(self, attr):
        try:
            return getattr(self.listControl, attr)
        except AttributeError:
            return object.Object.__getattr__(self, attr)

    def ItemFromHandle(self, handle):
        return self.itemHandleMap[handle]

    def SetStyle(self, newStyle):
        hwnd = self.listControl.GetSafeHwnd()
        style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
        win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, (style | newStyle))

    def HierInit(self, parent, listControl=None):  # Used when window first exists.
        # 039110.python.hierlist.line86.comment this also calls "Create" on the listbox.
        # 039111.python.hierlist.line87.comment params - id of listbbox, ID of bitmap, size of bitmaps
        if self.bitmapMask is None:
            bitmapMask = RGB(0, 0, 255)
        else:
            bitmapMask = self.bitmapMask
        self.imageList = win32ui.CreateImageList(self.bitmapID, 16, 0, bitmapMask)
        if listControl is None:
            if self.listBoxId is None:
                self.listBoxId = win32ui.IDC_LIST1
            self.listControl = parent.GetDlgItem(self.listBoxId)
        else:
            self.listControl = listControl
            lbid = listControl.GetDlgCtrlID()
            assert self.listBoxId is None or self.listBoxId == lbid, (
                "An invalid listbox control ID has been specified (specified as {}, but exists as {})".format(
                    self.listBoxId, lbid
                )
            )
            self.listBoxId = lbid
        self.listControl.SetImageList(self.imageList, commctrl.LVSIL_NORMAL)
        # 039112.python.hierlist.line107.comment self.list.AttachObject(self)

        parent.HookNotify(self.OnTreeItemExpanding, commctrl.TVN_ITEMEXPANDINGW)
        parent.HookNotify(self.OnTreeItemSelChanged, commctrl.TVN_SELCHANGEDW)
        parent.HookNotify(self.OnTreeItemDoubleClick, commctrl.NM_DBLCLK)
        self.notify_parent = parent

        if self.root:
            self.AcceptRoot(self.root)

    def DeleteAllItems(self):
        self.listControl.DeleteAllItems()
        self.root = None
        self.itemHandleMap = {}
        self.filledItemHandlesMap = {}

    def HierTerm(self):
        # 039113.python.hierlist.line124.comment Don't want notifies as we kill the list.
        parent = self.notify_parent  # GetParentFrame()
        parent.HookNotify(None, commctrl.TVN_ITEMEXPANDINGW)
        parent.HookNotify(None, commctrl.TVN_SELCHANGEDW)
        parent.HookNotify(None, commctrl.NM_DBLCLK)

        self.DeleteAllItems()
        self.listControl = None
        self.notify_parent = None  # Break a possible cycle

    def OnTreeItemDoubleClick(self, info, extra):
        (hwndFrom, idFrom, code) = info
        if idFrom != self.listBoxId:
            return None
        item = self.itemHandleMap[self.listControl.GetSelectedItem()]
        self.TakeDefaultAction(item)
        return 1

    def OnTreeItemExpanding(self, info, extra):
        (hwndFrom, idFrom, code) = info
        if idFrom != self.listBoxId:
            return None
        action, itemOld, itemNew, pt = extra
        itemHandle = itemNew[0]
        if itemHandle not in self.filledItemHandlesMap:
            item = self.itemHandleMap[itemHandle]
            self.AddSubList(itemHandle, self.GetSubList(item))
            self.filledItemHandlesMap[itemHandle] = None
        return 0

    def OnTreeItemSelChanged(self, info, extra):
        (hwndFrom, idFrom, code) = info
        if idFrom != self.listBoxId:
            return None
        action, itemOld, itemNew, pt = extra
        itemHandle = itemNew[0]
        item = self.itemHandleMap[itemHandle]
        self.PerformItemSelected(item)
        return 1

    def AddSubList(self, parentHandle, subItems):
        for item in subItems:
            self.AddItem(parentHandle, item)

    def AddItem(self, parentHandle, item, hInsertAfter=commctrl.TVI_LAST):
        text = self.GetText(item)
        if self.IsExpandable(item):
            cItems = 1  # Trick it !!
        else:
            cItems = 0
        bitmapCol = self.GetBitmapColumn(item)
        bitmapSel = self.GetSelectedBitmapColumn(item)
        if bitmapSel is None:
            bitmapSel = bitmapCol
        hitem = self.listControl.InsertItem(
            parentHandle,
            hInsertAfter,
            (None, None, None, text, bitmapCol, bitmapSel, cItems, 0),
        )
        self.itemHandleMap[hitem] = item
        return hitem

    def _GetChildHandles(self, handle):
        ret = []
        try:
            handle = self.listControl.GetChildItem(handle)
            while 1:
                ret.append(handle)
                handle = self.listControl.GetNextItem(handle, commctrl.TVGN_NEXT)
        except win32ui.error:
            # 039117.python.hierlist.line194.comment out of children
            pass
        return ret

    def Refresh(self, hparent=None):
        # 039118.python.hierlist.line199.comment Attempt to refresh the given item's sub-entries, but maintain the tree state
        # 039119.python.hierlist.line200.comment (ie, the selected item, expanded items, etc)
        if hparent is None:
            hparent = commctrl.TVI_ROOT
        if hparent not in self.filledItemHandlesMap:
            # 039120.python.hierlist.line204.comment This item has never been expanded, so no refresh can possibly be required.
            return
        root_item = self.itemHandleMap[hparent]
        old_handles = self._GetChildHandles(hparent)
        old_items = list(map(self.ItemFromHandle, old_handles))
        new_items = self.GetSubList(root_item)
        # 039121.python.hierlist.line210.comment Now an inefficient technique for synching the items.
        inew = 0
        hAfter = commctrl.TVI_FIRST
        for iold in range(len(old_items)):
            inewlook = inew
            matched = 0
            while inewlook < len(new_items):
                if old_items[iold] == new_items[inewlook]:
                    matched = 1
                    break
                inewlook += 1
            if matched:
                # 039122.python.hierlist.line222.comment Insert the new items.
                # 039123.python.hierlist.line223.comment print("Inserting after", old_items[iold], old_handles[iold])
                for i in range(inew, inewlook):
                    # 039124.python.hierlist.line225.comment print(f"Inserting index {i} ({new_items[i]})")
                    hAfter = self.AddItem(hparent, new_items[i], hAfter)

                inew = inewlook + 1
                # 039125.python.hierlist.line229.comment And recursively refresh iold
                hold = old_handles[iold]
                if hold in self.filledItemHandlesMap:
                    self.Refresh(hold)
            else:
                # 039126.python.hierlist.line234.comment Remove the deleted items.
                # 039127.python.hierlist.line235.comment print(f"Deleting {iold} ({old_items[iold]})")
                hdelete = old_handles[iold]
                # 039128.python.hierlist.line237.comment First recurse and remove the children from the map.
                for hchild in self._GetChildHandles(hdelete):
                    del self.itemHandleMap[hchild]
                    if hchild in self.filledItemHandlesMap:
                        del self.filledItemHandlesMap[hchild]
                self.listControl.DeleteItem(hdelete)
            hAfter = old_handles[iold]
        # 039129.python.hierlist.line244.comment Fill any remaining new items:
        for newItem in new_items[inew:]:
            # 039130.python.hierlist.line246.comment print("Inserting new item", newItem)
            self.AddItem(hparent, newItem)

    def AcceptRoot(self, root):
        self.listControl.DeleteAllItems()
        self.itemHandleMap = {commctrl.TVI_ROOT: root}
        self.filledItemHandlesMap = {commctrl.TVI_ROOT: root}
        subItems = self.GetSubList(root)
        self.AddSubList(0, subItems)

    def GetBitmapColumn(self, item):
        if self.IsExpandable(item):
            return 0
        else:
            return 4

    def GetSelectedBitmapColumn(self, item) -> int | None:
        return 0

    def CheckChangedChildren(self):
        return self.listControl.CheckChangedChildren()

    def GetText(self, item):
        return GetItemText(item)

    def PerformItemSelected(self, item):
        try:
            win32ui.SetStatusText("Selected " + self.GetText(item))
        except win32ui.error:  # No status bar!
            pass

    def TakeDefaultAction(self, item):
        win32ui.MessageBox("Got item " + self.GetText(item))


# 039132.python.hierlist.line281.comment #########################################################################
# 039133.python.hierlist.line282.comment
# 039134.python.hierlist.line283.comment Classes for use with seperate HierListItems.
# 039135.python.hierlist.line284.comment
# 039136.python.hierlist.line285.comment
class HierListWithItems(HierList):
    def __init__(
        self, root, bitmapID=win32ui.IDB_HIERFOLDERS, listBoxID=None, bitmapMask=None
    ):  # used to create object.
        HierList.__init__(self, root, bitmapID, listBoxID, bitmapMask)

    def DelegateCall(self, fn):
        return fn()

    def GetBitmapColumn(self, item):
        rc = self.DelegateCall(item.GetBitmapColumn)
        if rc is None:
            rc = HierList.GetBitmapColumn(self, item)
        return rc

    def GetSelectedBitmapColumn(self, item):
        return self.DelegateCall(item.GetSelectedBitmapColumn)

    def IsExpandable(self, item):
        return self.DelegateCall(item.IsExpandable)

    def GetText(self, item):
        return self.DelegateCall(item.GetText)

    def GetSubList(self, item):
        return self.DelegateCall(item.GetSubList)

    def PerformItemSelected(self, item):
        func = getattr(item, "PerformItemSelected", None)
        if func is None:
            return HierList.PerformItemSelected(self, item)
        else:
            return self.DelegateCall(func)

    def TakeDefaultAction(self, item):
        func = getattr(item, "TakeDefaultAction", None)
        if func is None:
            return HierList.TakeDefaultAction(self, item)
        else:
            return self.DelegateCall(func)


# 039138.python.hierlist.line328.comment A hier list item - for use with a HierListWithItems
class HierListItem:
    def __init__(self):
        pass

    def GetText(self):
        pass

    def GetSubList(self):
        pass

    def IsExpandable(self):
        pass

    def GetBitmapColumn(self):
        return None  # indicate he should do it.

    def GetSelectedBitmapColumn(self):
        return None  # same as other

    def __lt__(self, other):
        # 039141.python.hierlist.line349.comment we want unrelated items to be sortable...
        return id(self) < id(other)

    def __eq__(self, other):
        return False
