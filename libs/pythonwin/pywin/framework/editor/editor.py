# 037503.python.editor.line1.comment ####################################################################
# 037504.python.editor.line2.comment
# 037505.python.editor.line3.comment editor.py
# 037506.python.editor.line4.comment
# 037507.python.editor.line5.comment A general purpose text editor, built on top of the win32ui edit
# 037508.python.editor.line6.comment type, which is built on an MFC CEditView
# 037509.python.editor.line7.comment
# 037510.python.editor.line8.comment
# 037511.python.editor.line9.comment We now support reloading of externally modified documented
# 037512.python.editor.line10.comment (eg, presumably by some other process, such as source control or
# 037513.python.editor.line11.comment another editor.
# 037514.python.editor.line12.comment We also support auto-loading of externally modified files.
# 037515.python.editor.line13.comment - if the current document has not been modified in this
# 037516.python.editor.line14.comment editor, but has been modified on disk, then the file
# 037517.python.editor.line15.comment can be automatically reloaded.
# 037518.python.editor.line16.comment
# 037519.python.editor.line17.comment Note that it will _always_ prompt you if the file in the editor has been modified.


import re

import win32api
import win32con
import win32ui
from pywin.framework.editor import (
    GetEditorFontOption,
    GetEditorOption,
    defaultCharacterFormat,
)
from pywin.mfc import afxres
from pywin.mfc.docview import RichEditView as ParentEditorView

from .document import EditorDocumentBase as ParentEditorDocument

# 037520.python.editor.line35.comment from pywin.mfc.docview import EditView as ParentEditorView
# 037521.python.editor.line36.comment from pywin.mfc.docview import Document as ParentEditorDocument

patImport = re.compile(r"import (?P<name>.*)")
patIndent = re.compile(r"^([ \t]*[~ \t])")

ID_LOCATE_FILE = 0xE200
ID_GOTO_LINE = 0xE2001
# 037522.python.editor.line43.comment WARNING: Duplicated in document.py and coloreditor.py
MSG_CHECK_EXTERNAL_FILE = win32con.WM_USER + 1999

# 037523.python.editor.line46.comment Key Codes that modify the bufffer when Ctrl or Alt are NOT pressed.
MODIFYING_VK_KEYS = [
    win32con.VK_BACK,
    win32con.VK_TAB,
    win32con.VK_RETURN,
    win32con.VK_SPACE,
    win32con.VK_DELETE,
]
for k in range(48, 91):
    MODIFYING_VK_KEYS.append(k)

# 037524.python.editor.line57.comment Key Codes that modify the bufffer when Ctrl is pressed.
MODIFYING_VK_KEYS_CTRL = [
    win32con.VK_BACK,
    win32con.VK_RETURN,
    win32con.VK_SPACE,
    win32con.VK_DELETE,
]

# 037525.python.editor.line65.comment Key Codes that modify the bufffer when Alt is pressed.
MODIFYING_VK_KEYS_ALT = [
    win32con.VK_BACK,
    win32con.VK_RETURN,
    win32con.VK_SPACE,
    win32con.VK_DELETE,
]


# 037526.python.editor.line74.comment The editor itself starts here.
# 037527.python.editor.line75.comment Using the MFC Document/View model, we have an EditorDocument, which is responsible for
# 037528.python.editor.line76.comment managing the contents of the file, and a view which is responsible for rendering it.
# 037529.python.editor.line77.comment
# 037530.python.editor.line78.comment Due to a limitation in the Windows edit controls, we are limited to one view
# 037531.python.editor.line79.comment per document, although nothing in this code assumes this (I hope!)

isRichText = 1  # We are using the Rich Text control.  This has not been tested with value "0" for quite some time!


class EditorDocument(ParentEditorDocument):
    # 037533.python.editor.line85.comment
    # 037534.python.editor.line86.comment File loading and saving operations
    # 037535.python.editor.line87.comment
    def OnOpenDocument(self, filename):
        # 037536.python.editor.line89.comment
        # 037537.python.editor.line90.comment handle Unix and PC text file format.
        # 037538.python.editor.line91.comment

        # 037539.python.editor.line93.comment Get the "long name" of the file name, as it may have been translated
        # 037540.python.editor.line94.comment to short names by the shell.
        self.SetPathName(filename)  # Must set this early!
        # 037542.python.editor.line96.comment Now do the work!
        self.BeginWaitCursor()
        win32ui.SetStatusText("Loading file...", 1)
        try:
            f = open(filename, "rb")
        except OSError:
            win32ui.MessageBox(
                filename
                + "\nCan not find this file\nPlease verify that the correct path and file name are given"
            )
            self.EndWaitCursor()
            return 0
        raw = f.read()
        f.close()
        contents = self.TranslateLoadedData(raw)
        rc = 0
        try:
            self.GetFirstView().SetWindowText(contents)
            rc = 1
        except TypeError:  # Null byte in file.
            win32ui.MessageBox("This file contains NULL bytes, and can not be edited")
            rc = 0

        self.EndWaitCursor()
        self.SetModifiedFlag(0)  # No longer dirty
        self._DocumentStateChanged()
        return rc

    def TranslateLoadedData(self, data):
        """Given raw data read from a file, massage it suitable for the edit window"""
        # 037545.python.editor.line126.comment if a CR in the first 250 chars, then perform the expensive translate
        if data[:250].find("\r") == -1:
            win32ui.SetStatusText(
                "Translating from Unix file format - please wait...", 1
            )
            return re.sub(r"\r*\n", "\r\n", data)
        else:
            return data

    def SaveFile(self, fileName, encoding=None):
        if isRichText:
            view = self.GetFirstView()
            view.SaveTextFile(fileName, encoding=encoding)
        else:  # Old style edit view window.
            self.GetFirstView().SaveFile(fileName)
        try:
            # 037547.python.editor.line142.comment Make sure line cache has updated info about me!
            import linecache

            linecache.checkcache()
        except:
            pass

    # 037548.python.editor.line149.comment
    # 037549.python.editor.line150.comment Color state stuff
    # 037550.python.editor.line151.comment
    def SetAllLineColors(self, color=None):
        for view in self.GetAllViews():
            view.SetAllLineColors(color)

    def SetLineColor(self, lineNo, color):
        "Color a line of all views"
        for view in self.GetAllViews():
            view.SetLineColor(lineNo, color)


# 037551.python.editor.line162.comment def StreamTextOut(self, data): ### This seems unreliable???
# 037552.python.editor.line163.comment self.saveFileHandle.write(data)
# 037553.python.editor.line164.comment return 1 # keep em coming!


class EditorView(ParentEditorView):
    def __init__(self, doc):
        ParentEditorView.__init__(self, doc)
        if isRichText:
            self.SetWordWrap(win32ui.CRichEditView_WrapNone)

        self.addToMRU = 1
        self.HookHandlers()
        self.bCheckingFile = 0

        self.defCharFormat = GetEditorFontOption("Default Font", defaultCharacterFormat)

        # 037554.python.editor.line179.comment Smart tabs override everything else if context can be worked out.
        self.bSmartTabs = GetEditorOption("Smart Tabs", 1)

        self.tabSize = GetEditorOption("Tab Size", 8)
        self.indentSize = GetEditorOption("Indent Size", 8)
        # 037555.python.editor.line184.comment If next indent is at a tab position, and useTabs is set, a tab will be inserted.
        self.bUseTabs = GetEditorOption("Use Tabs", 1)

    def OnInitialUpdate(self):
        rc = self._obj_.OnInitialUpdate()
        self.SetDefaultCharFormat(self.defCharFormat)
        return rc

    def CutCurLine(self):
        curLine = self._obj_.LineFromChar()
        nextLine = curLine + 1
        start = self._obj_.LineIndex(curLine)
        end = self._obj_.LineIndex(nextLine)
        if end == 0:  # must be last line.
            end = start + self.end.GetLineLength(curLine)
        self._obj_.SetSel(start, end)
        self._obj_.Cut()

    def _PrepareUserStateChange(self):
        "Return selection, lineindex, etc info, so it can be restored"
        self.SetRedraw(0)
        return self.GetModify(), self.GetSel(), self.GetFirstVisibleLine()

    def _EndUserStateChange(self, info):
        scrollOff = info[2] - self.GetFirstVisibleLine()
        if scrollOff:
            self.LineScroll(scrollOff)
        self.SetSel(info[1])
        self.SetModify(info[0])
        self.SetRedraw(1)
        self.InvalidateRect()
        self.UpdateWindow()

    def _UpdateUIForState(self):
        self.SetReadOnly(self.GetDocument()._IsReadOnly())

    def SetAllLineColors(self, color=None):
        if isRichText:
            info = self._PrepareUserStateChange()
            try:
                if color is None:
                    color = self.defCharFormat[4]
                self.SetSel(0, -1)
                self.SetSelectionCharFormat((win32con.CFM_COLOR, 0, 0, 0, color))
            finally:
                self._EndUserStateChange(info)

    def SetLineColor(self, lineNo, color):
        "lineNo is the 1 based line number to set.  If color is None, default color is used."
        if isRichText:
            info = self._PrepareUserStateChange()
            try:
                if color is None:
                    color = self.defCharFormat[4]
                lineNo -= 1
                startIndex = self.LineIndex(lineNo)
                if startIndex != -1:
                    self.SetSel(startIndex, self.LineIndex(lineNo + 1))
                    self.SetSelectionCharFormat((win32con.CFM_COLOR, 0, 0, 0, color))
            finally:
                self._EndUserStateChange(info)

    def Indent(self):
        """Insert an indent to move the cursor to the next tab position.

        Honors the tab size and 'use tabs' settings.  Assumes the cursor is already at the
        position to be indented, and the selection is a single character (ie, not a block)
        """
        start, end = self._obj_.GetSel()
        startLine = self._obj_.LineFromChar(start)
        line = self._obj_.GetLine(startLine)
        realCol = start - self._obj_.LineIndex(startLine)
        # 037557.python.editor.line256.comment Calulate the next tab stop.
        # 037558.python.editor.line257.comment Expand existing tabs.
        curCol = 0
        for ch in line[:realCol]:
            if ch == "\t":
                curCol = ((curCol / self.tabSize) + 1) * self.tabSize
            else:
                curCol += 1
        nextColumn = ((curCol / self.indentSize) + 1) * self.indentSize
        # 037559.python.editor.line265.comment print("curCol is", curCol, "nextColumn is", nextColumn)
        ins = None
        if self.bSmartTabs:
            # 037560.python.editor.line268.comment Look for some context.
            if realCol == 0:  # Start of the line - see if the line above can tell us
                lookLine = startLine - 1
                while lookLine >= 0:
                    check = self._obj_.GetLine(lookLine)[0:1]
                    if check in ("\t", " "):
                        ins = check
                        break
                    lookLine -= 1
            else:  # See if the previous char can tell us
                check = line[realCol - 1]
                if check in ("\t", " "):
                    ins = check

        # 037563.python.editor.line282.comment Either smart tabs off, or not smart enough!
        # 037564.python.editor.line283.comment Use the "old style" settings.
        if ins is None:
            if self.bUseTabs and nextColumn % self.tabSize == 0:
                ins = "\t"
            else:
                ins = " "

        if ins == " ":
            # 037565.python.editor.line291.comment Calc the number of spaces to take us to the next stop
            ins *= nextColumn - curCol

        self._obj_.ReplaceSel(ins)

    def BlockDent(self, isIndent, startLine, endLine):
        "Indent/Undent all lines specified"
        if not self.GetDocument().CheckMakeDocumentWritable():
            return 0
        tabSize = self.tabSize  # hard-code for now!
        info = self._PrepareUserStateChange()
        try:
            for lineNo in range(startLine, endLine):
                pos = self._obj_.LineIndex(lineNo)
                self._obj_.SetSel(pos, pos)
                if isIndent:
                    self.Indent()
                else:
                    line = self._obj_.GetLine(lineNo)
                    try:
                        noToDel = 0
                        if line[0] == "\t":
                            noToDel = 1
                        elif line[0] == " ":
                            for noToDel in range(0, tabSize):
                                if line[noToDel] != " ":
                                    break
                            else:
                                noToDel = tabSize
                        if noToDel:
                            self._obj_.SetSel(pos, pos + noToDel)
                            self._obj_.Clear()
                    except IndexError:
                        pass
        finally:
            self._EndUserStateChange(info)
        self.GetDocument().SetModifiedFlag(1)  # Now dirty
        self._obj_.SetSel(self.LineIndex(startLine), self.LineIndex(endLine))

    def GotoLine(self, lineNo=None):
        try:
            if lineNo is None:
                lineNo = int(input("Enter Line Number"))
        except (ValueError, KeyboardInterrupt):
            return 0
        self.GetLineCount()  # Seems to be needed when file first opened???
        charNo = self.LineIndex(lineNo - 1)
        self.SetSel(charNo)

    def HookHandlers(self):  # children can override, but should still call me!
        # 037570.python.editor.line341.comment self.HookAllKeyStrokes(self.OnKey)
        self.HookMessage(self.OnCheckExternalDocumentUpdated, MSG_CHECK_EXTERNAL_FILE)
        self.HookMessage(self.OnRClick, win32con.WM_RBUTTONDOWN)
        self.HookMessage(self.OnSetFocus, win32con.WM_SETFOCUS)
        self.HookMessage(self.OnKeyDown, win32con.WM_KEYDOWN)
        self.HookKeyStroke(self.OnKeyCtrlY, 25)  # ^Y
        self.HookKeyStroke(self.OnKeyCtrlG, 7)  # ^G
        self.HookKeyStroke(self.OnKeyTab, 9)  # TAB
        self.HookKeyStroke(self.OnKeyEnter, 13)  # Enter
        self.HookCommand(self.OnCmdLocateFile, ID_LOCATE_FILE)
        self.HookCommand(self.OnCmdGotoLine, ID_GOTO_LINE)
        self.HookCommand(self.OnEditPaste, afxres.ID_EDIT_PASTE)
        self.HookCommand(self.OnEditCut, afxres.ID_EDIT_CUT)

    # 037575.python.editor.line355.comment Hook Handlers
    def OnSetFocus(self, msg):
        # 037576.python.editor.line357.comment Even though we use file change notifications, we should be very sure about it here.
        self.OnCheckExternalDocumentUpdated(msg)

    def OnRClick(self, params):
        menu = win32ui.CreatePopupMenu()

        # 037577.python.editor.line363.comment look for a module name
        line = self._obj_.GetLine().strip()
        flags = win32con.MF_STRING | win32con.MF_ENABLED
        matchResult = patImport.match(line)
        if matchResult and matchResult[0] == line:
            menu.AppendMenu(
                flags, ID_LOCATE_FILE, "&Locate %s.py" % matchResult.group("name")
            )
            menu.AppendMenu(win32con.MF_SEPARATOR)
        menu.AppendMenu(flags, win32ui.ID_EDIT_UNDO, "&Undo")
        menu.AppendMenu(win32con.MF_SEPARATOR)
        menu.AppendMenu(flags, win32ui.ID_EDIT_CUT, "Cu&t")
        menu.AppendMenu(flags, win32ui.ID_EDIT_COPY, "&Copy")
        menu.AppendMenu(flags, win32ui.ID_EDIT_PASTE, "&Paste")
        menu.AppendMenu(flags, win32con.MF_SEPARATOR)
        menu.AppendMenu(flags, win32ui.ID_EDIT_SELECT_ALL, "&Select all")
        menu.AppendMenu(flags, win32con.MF_SEPARATOR)
        menu.AppendMenu(flags, ID_GOTO_LINE, "&Goto line...")
        menu.TrackPopupMenu(params[5])
        return 0

    def OnCmdGotoLine(self, cmd, code):
        self.GotoLine()
        return 0

    def OnCmdLocateFile(self, cmd, code):
        modName = patImport.group("name")
        if not modName:
            return 0
        import pywin.framework.scriptutils

        fileName = pywin.framework.scriptutils.LocatePythonFile(modName)
        if fileName is None:
            win32ui.SetStatusText("Can't locate module %s" % modName)
        else:
            win32ui.GetApp().OpenDocumentFile(fileName)
        return 0

    # 037578.python.editor.line401.comment Key handlers
    def OnKeyEnter(self, key):
        if not self.GetDocument().CheckMakeDocumentWritable():
            return 0
        curLine = self._obj_.GetLine()
        self._obj_.ReplaceSel("\r\n")  # insert the newline
        # 037580.python.editor.line407.comment If the current line indicates the next should be indented,
        # 037581.python.editor.line408.comment then copy the current indentation to this line.
        res = patIndent.match(curLine, 0)
        if res > 0 and curLine.strip():
            curIndent = patIndent.group(1)
            self._obj_.ReplaceSel(curIndent)
        return 0  # don't pass on

    def OnKeyCtrlY(self, key):
        if not self.GetDocument().CheckMakeDocumentWritable():
            return 0
        self.CutCurLine()
        return 0  # don't let him have it!

    def OnKeyCtrlG(self, key):
        self.GotoLine()
        return 0  # don't let him have it!

    def OnKeyTab(self, key):
        if not self.GetDocument().CheckMakeDocumentWritable():
            return 0
        start, end = self._obj_.GetSel()
        if start == end:  # normal TAB key
            self.Indent()
            return 0  # we handled this.

        # 037587.python.editor.line433.comment Otherwise it is a block indent/dedent.
        if start > end:
            start, end = end, start  # swap them.
        startLine = self._obj_.LineFromChar(start)
        endLine = self._obj_.LineFromChar(end)

        self.BlockDent(win32api.GetKeyState(win32con.VK_SHIFT) >= 0, startLine, endLine)
        return 0

    def OnEditPaste(self, id, code):
        # 037589.python.editor.line443.comment Return 1 if we can make the file editable.(or it already is!)
        return self.GetDocument().CheckMakeDocumentWritable()

    def OnEditCut(self, id, code):
        # 037590.python.editor.line447.comment Return 1 if we can make the file editable.(or it already is!)
        return self.GetDocument().CheckMakeDocumentWritable()

    def OnKeyDown(self, msg):
        key = msg[2]
        if win32api.GetKeyState(win32con.VK_CONTROL) & 0x8000:
            modList = MODIFYING_VK_KEYS_CTRL
        elif win32api.GetKeyState(win32con.VK_MENU) & 0x8000:
            modList = MODIFYING_VK_KEYS_ALT
        else:
            modList = MODIFYING_VK_KEYS

        if key in modList:
            # 037591.python.editor.line460.comment Return 1 if we can make the file editable.(or it already is!)
            return self.GetDocument().CheckMakeDocumentWritable()
        return 1  # Pass it on OK

    # 037593.python.editor.line464.comment def OnKey(self, key):
    # 037594.python.editor.line465.comment return self.GetDocument().CheckMakeDocumentWritable()

    def OnCheckExternalDocumentUpdated(self, msg):
        if self._obj_ is None or self.bCheckingFile:
            return
        self.bCheckingFile = 1
        self.GetDocument().CheckExternalDocumentUpdated()
        self.bCheckingFile = 0


from .template import EditorTemplateBase


class EditorTemplate(EditorTemplateBase):
    def __init__(
        self, res=win32ui.IDR_TEXTTYPE, makeDoc=None, makeFrame=None, makeView=None
    ):
        if makeDoc is None:
            makeDoc = EditorDocument
        if makeView is None:
            makeView = EditorView
        EditorTemplateBase.__init__(self, res, makeDoc, makeFrame, makeView)

    def _CreateDocTemplate(self, resourceId):
        return win32ui.CreateRichEditDocTemplate(resourceId)

    def CreateWin32uiDocument(self):
        return self.DoCreateRichEditDoc()


def Create(fileName=None, title=None, template=None):
    return editorTemplate.OpenDocumentFile(fileName)


from pywin.framework.editor import GetDefaultEditorModuleName

prefModule = GetDefaultEditorModuleName()
# 037595.python.editor.line502.comment Initialize only if this is the "default" editor.
if __name__ == prefModule:
    # 037596.python.editor.line504.comment For debugging purposes, when this module may be reloaded many times.
    try:
        win32ui.GetApp().RemoveDocTemplate(editorTemplate)  # type: ignore[has-type, used-before-def]
    except (NameError, win32ui.error):
        pass

    editorTemplate = EditorTemplate()
    win32ui.GetApp().AddDocTemplate(editorTemplate)
