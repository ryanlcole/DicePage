# 038060.python.toolmenu.line1.comment toolmenu.py

import sys

import win32api
import win32con
import win32ui

tools = {}
idPos = 100

# 038061.python.toolmenu.line12.comment The default items should no tools menu exist in the INI file.
defaultToolMenuItems = [
    ("Browser", "win32ui.GetApp().OnViewBrowse(0,0)"),
    (
        "Browse PythonPath",
        "from pywin.tools import browseProjects;browseProjects.Browse()",
    ),
    ("Edit Python Path", "from pywin.tools import regedit;regedit.EditRegistry()"),
    ("COM Makepy utility", "from win32com.client import makepy;makepy.main()"),
    (
        "COM Browser",
        "from win32com.client import combrowse;combrowse.main(modal=False)",
    ),
    (
        "Trace Collector Debugging tool",
        "from pywin.tools import TraceCollector;TraceCollector.MakeOutputWindow()",
    ),
]


def LoadToolMenuItems():
    # 038062.python.toolmenu.line33.comment Load from the registry.
    items = []
    lookNo = 1
    while 1:
        menu = win32ui.GetProfileVal("Tools Menu\\%s" % lookNo, "", "")
        if menu == "":
            break
        cmd = win32ui.GetProfileVal("Tools Menu\\%s" % lookNo, "Command", "")
        items.append((menu, cmd))
        lookNo += 1

    if len(items) == 0:
        items = defaultToolMenuItems
    return items


def WriteToolMenuItems(items):
    # 038063.python.toolmenu.line50.comment Items is a list of (menu, command)
    # 038064.python.toolmenu.line51.comment Delete the entire registry tree.
    try:
        mainKey = win32ui.GetAppRegistryKey()
        toolKey = win32api.RegOpenKey(mainKey, "Tools Menu")
    except win32ui.error:
        toolKey = None
    if toolKey is not None:
        while 1:
            try:
                subkey = win32api.RegEnumKey(toolKey, 0)
            except win32api.error:
                break
            win32api.RegDeleteKey(toolKey, subkey)
    # 038065.python.toolmenu.line64.comment Keys are now removed - write the new ones.
    # 038066.python.toolmenu.line65.comment But first check if we have the defaults - and if so, don't write anything!
    if items == defaultToolMenuItems:
        return
    itemNo = 1
    for menu, cmd in items:
        win32ui.WriteProfileVal("Tools Menu\\%s" % itemNo, "", menu)
        win32ui.WriteProfileVal("Tools Menu\\%s" % itemNo, "Command", cmd)
        itemNo += 1


def SetToolsMenu(menu, menuPos=None):
    global tools
    global idPos

    # 038067.python.toolmenu.line79.comment todo - check the menu does not already exist.
    # 038068.python.toolmenu.line80.comment Create the new menu
    toolsMenu = win32ui.CreatePopupMenu()

    # 038069.python.toolmenu.line83.comment Load from the ini file.
    items = LoadToolMenuItems()
    for menuString, cmd in items:
        tools[idPos] = (menuString, cmd, menuString)
        toolsMenu.AppendMenu(
            win32con.MF_ENABLED | win32con.MF_STRING, idPos, menuString
        )
        win32ui.GetMainFrame().HookCommand(HandleToolCommand, idPos)
        idPos += 1

    # 038070.python.toolmenu.line93.comment Find the correct spot to insert the new tools menu.
    if menuPos is None:
        menuPos = menu.GetMenuItemCount() - 2
        if menuPos < 0:
            menuPos = 0

    menu.InsertMenu(
        menuPos,
        win32con.MF_BYPOSITION
        | win32con.MF_ENABLED
        | win32con.MF_STRING
        | win32con.MF_POPUP,
        toolsMenu.GetHandle(),
        "&Tools",
    )


def HandleToolCommand(cmd, code):
    import re
    import traceback

    global tools
    (menuString, pyCmd, desc) = tools[cmd]
    win32ui.SetStatusText("Executing tool %s" % desc, 1)
    pyCmd = re.sub(r"\\n", "\n", pyCmd)
    win32ui.DoWaitCursor(1)
    oldFlag = None
    try:
        oldFlag = sys.stdout.template.writeQueueing
        sys.stdout.template.writeQueueing = 0
    except (NameError, AttributeError):
        pass

    try:
        exec("%s\n" % pyCmd)
        worked = 1
    except SystemExit:
        # 038071.python.toolmenu.line130.comment The program raised a SystemExit - ignore it.
        worked = 1
    except:
        print("Failed to execute command:\n%s" % pyCmd)
        traceback.print_exc()
        worked = 0
    if oldFlag is not None:
        sys.stdout.template.writeQueueing = oldFlag
    win32ui.DoWaitCursor(0)
    if worked:
        text = "Completed successfully."
    else:
        text = "Error executing %s." % desc
    win32ui.SetStatusText(text, 1)


# 038072.python.toolmenu.line146.comment The property page for maintaing the items on the Tools menu.
import commctrl
from pywin.mfc import dialog

LVN_ENDLABELEDIT = commctrl.LVN_ENDLABELEDITW


class ToolMenuPropPage(dialog.PropertyPage):
    def __init__(self):
        self.bImChangingEditControls = 0  # Am I programatically changing the controls?
        dialog.PropertyPage.__init__(self, win32ui.IDD_PP_TOOLMENU)

    def OnInitDialog(self):
        self.editMenuCommand = self.GetDlgItem(win32ui.IDC_EDIT2)
        self.butNew = self.GetDlgItem(win32ui.IDC_BUTTON3)

        # 038074.python.toolmenu.line162.comment Now hook the change notification messages for the edit controls.
        self.HookCommand(self.OnCommandEditControls, win32ui.IDC_EDIT1)
        self.HookCommand(self.OnCommandEditControls, win32ui.IDC_EDIT2)

        self.HookNotify(self.OnNotifyListControl, commctrl.LVN_ITEMCHANGED)
        self.HookNotify(self.OnNotifyListControlEndLabelEdit, commctrl.LVN_ENDLABELEDIT)

        # 038075.python.toolmenu.line169.comment Hook the button clicks.
        self.HookCommand(self.OnButtonNew, win32ui.IDC_BUTTON3)  # New Item
        self.HookCommand(self.OnButtonDelete, win32ui.IDC_BUTTON4)  # Delete item
        self.HookCommand(self.OnButtonMove, win32ui.IDC_BUTTON1)  # Move up
        self.HookCommand(self.OnButtonMove, win32ui.IDC_BUTTON2)  # Move down

        # 038080.python.toolmenu.line175.comment Setup the columns in the list control
        lc = self.GetDlgItem(win32ui.IDC_LIST1)
        rect = lc.GetWindowRect()
        cx = rect[2] - rect[0]
        colSize = cx / 2 - win32api.GetSystemMetrics(win32con.SM_CXBORDER) - 1

        item = commctrl.LVCFMT_LEFT, colSize, "Menu Text"
        lc.InsertColumn(0, item)

        item = commctrl.LVCFMT_LEFT, colSize, "Python Command"
        lc.InsertColumn(1, item)

        # 038081.python.toolmenu.line187.comment Insert the existing tools menu
        itemNo = 0
        for desc, cmd in LoadToolMenuItems():
            lc.InsertItem(itemNo, desc)
            lc.SetItemText(itemNo, 1, cmd)
            itemNo += 1

        self.listControl = lc
        return dialog.PropertyPage.OnInitDialog(self)

    def OnOK(self):
        # 038082.python.toolmenu.line198.comment Write the menu back to the registry.
        items = []
        itemLook = 0
        while 1:
            try:
                text = self.listControl.GetItemText(itemLook, 0)
                if not text:
                    break
                items.append((text, self.listControl.GetItemText(itemLook, 1)))
            except win32ui.error:
                # 038083.python.toolmenu.line208.comment no more items!
                break
            itemLook += 1
        WriteToolMenuItems(items)
        return self._obj_.OnOK()

    def OnCommandEditControls(self, id, cmd):
        # 038084.python.toolmenu.line215.comment print("OnEditControls", id, cmd)
        if cmd == win32con.EN_CHANGE and not self.bImChangingEditControls:
            itemNo = self.listControl.GetNextItem(-1, commctrl.LVNI_SELECTED)
            newText = self.editMenuCommand.GetWindowText()
            self.listControl.SetItemText(itemNo, 1, newText)

        return 0

    def OnNotifyListControlEndLabelEdit(self, id, cmd):
        newText = self.listControl.GetEditControl().GetWindowText()
        itemNo = self.listControl.GetNextItem(-1, commctrl.LVNI_SELECTED)
        self.listControl.SetItemText(itemNo, 0, newText)

    def OnNotifyListControl(self, id, cmd):
        # 038085.python.toolmenu.line229.comment print(id, cmd)
        try:
            itemNo = self.listControl.GetNextItem(-1, commctrl.LVNI_SELECTED)
        except win32ui.error:  # No selection!
            return

        self.bImChangingEditControls = 1
        try:
            item = self.listControl.GetItem(itemNo, 1)
            self.editMenuCommand.SetWindowText(item[4])
        finally:
            self.bImChangingEditControls = 0

        return 0  # we have handled this!

    def OnButtonNew(self, id, cmd):
        if cmd == win32con.BN_CLICKED:
            newIndex = self.listControl.GetItemCount()
            self.listControl.InsertItem(newIndex, "Click to edit the text")
            self.listControl.EnsureVisible(newIndex, 0)

    def OnButtonMove(self, id, cmd):
        if cmd == win32con.BN_CLICKED:
            try:
                itemNo = self.listControl.GetNextItem(-1, commctrl.LVNI_SELECTED)
            except win32ui.error:
                return
            menu = self.listControl.GetItemText(itemNo, 0)
            cmd = self.listControl.GetItemText(itemNo, 1)
            if id == win32ui.IDC_BUTTON1:
                # 038088.python.toolmenu.line259.comment Move up
                if itemNo > 0:
                    self.listControl.DeleteItem(itemNo)
                    # 038089.python.toolmenu.line262.comment reinsert it.
                    self.listControl.InsertItem(itemNo - 1, menu)
                    self.listControl.SetItemText(itemNo - 1, 1, cmd)
            else:
                # 038090.python.toolmenu.line266.comment Move down.
                if itemNo < self.listControl.GetItemCount() - 1:
                    self.listControl.DeleteItem(itemNo)
                    # 038091.python.toolmenu.line269.comment reinsert it.
                    self.listControl.InsertItem(itemNo + 1, menu)
                    self.listControl.SetItemText(itemNo + 1, 1, cmd)

    def OnButtonDelete(self, id, cmd):
        if cmd == win32con.BN_CLICKED:
            try:
                itemNo = self.listControl.GetNextItem(-1, commctrl.LVNI_SELECTED)
            except win32ui.error:  # No selection!
                return
            self.listControl.DeleteItem(itemNo)
