# 038906.python.view.line1.comment A general purpose MFC CCtrlView view that uses Scintilla.

import os
import re
import string
import struct
import sys

import __main__  # for attribute lookup
import win32con
import win32ui
from pywin.mfc import afxres, docview

from . import (
    IDLEenvironment,  # nopycln: import # Injects fast_readline into the IDLE auto-indent extension
    bindings,
    control,
    scintillacon,
)

PRINTDLGORD = 1538
IDC_PRINT_MAG_EDIT = 1010
EM_FORMATRANGE = win32con.WM_USER + 57

wordbreaks = "._" + string.ascii_uppercase + string.ascii_lowercase + string.digits

patImport = re.compile(r"import (?P<name>.*)")

_event_commands = [
    # 038909.python.view.line30.comment File menu
    "win32ui.ID_FILE_LOCATE",
    "win32ui.ID_FILE_CHECK",
    "afxres.ID_FILE_CLOSE",
    "afxres.ID_FILE_NEW",
    "afxres.ID_FILE_OPEN",
    "afxres.ID_FILE_SAVE",
    "afxres.ID_FILE_SAVE_AS",
    "win32ui.ID_FILE_SAVE_ALL",
    # 038910.python.view.line39.comment Edit menu
    "afxres.ID_EDIT_UNDO",
    "afxres.ID_EDIT_REDO",
    "afxres.ID_EDIT_CUT",
    "afxres.ID_EDIT_COPY",
    "afxres.ID_EDIT_PASTE",
    "afxres.ID_EDIT_SELECT_ALL",
    "afxres.ID_EDIT_FIND",
    "afxres.ID_EDIT_REPEAT",
    "afxres.ID_EDIT_REPLACE",
    # 038911.python.view.line49.comment View menu
    "win32ui.ID_VIEW_WHITESPACE",
    "win32ui.ID_VIEW_FIXED_FONT",
    "win32ui.ID_VIEW_BROWSE",
    "win32ui.ID_VIEW_INTERACTIVE",
    # 038912.python.view.line54.comment Window menu
    "afxres.ID_WINDOW_ARRANGE",
    "afxres.ID_WINDOW_CASCADE",
    "afxres.ID_WINDOW_NEW",
    "afxres.ID_WINDOW_SPLIT",
    "afxres.ID_WINDOW_TILE_HORZ",
    "afxres.ID_WINDOW_TILE_VERT",
    # 038913.python.view.line61.comment Others
    "afxres.ID_APP_EXIT",
    "afxres.ID_APP_ABOUT",
]

_extra_event_commands = [
    ("EditDelete", afxres.ID_EDIT_CLEAR),
    ("LocateModule", win32ui.ID_FILE_LOCATE),
    ("GotoLine", win32ui.ID_EDIT_GOTO_LINE),
    ("DbgBreakpointToggle", win32ui.IDC_DBG_ADD),
    ("DbgGo", win32ui.IDC_DBG_GO),
    ("DbgStepOver", win32ui.IDC_DBG_STEPOVER),
    ("DbgStep", win32ui.IDC_DBG_STEP),
    ("DbgStepOut", win32ui.IDC_DBG_STEPOUT),
    ("DbgBreakpointClearAll", win32ui.IDC_DBG_CLEAR),
    ("DbgClose", win32ui.IDC_DBG_CLOSE),
]

event_commands = []


def _CreateEvents():
    for name in _event_commands:
        val = eval(name)
        name_parts = name.split("_")[1:]
        name_parts = [p.capitalize() for p in name_parts]
        event = "".join(name_parts)
        event_commands.append((event, val))
    for name, id in _extra_event_commands:
        event_commands.append((name, id))


_CreateEvents()
del _event_commands
del _extra_event_commands

command_reflectors = [
    (win32ui.ID_EDIT_UNDO, win32con.WM_UNDO),
    (win32ui.ID_EDIT_REDO, scintillacon.SCI_REDO),
    (win32ui.ID_EDIT_CUT, win32con.WM_CUT),
    (win32ui.ID_EDIT_COPY, win32con.WM_COPY),
    (win32ui.ID_EDIT_PASTE, win32con.WM_PASTE),
    (win32ui.ID_EDIT_CLEAR, win32con.WM_CLEAR),
    (win32ui.ID_EDIT_SELECT_ALL, scintillacon.SCI_SELECTALL),
]


def DoBraceMatch(control):
    curPos = control.SCIGetCurrentPos()
    charBefore = " "
    if curPos:
        charBefore = control.SCIGetCharAt(curPos - 1)
    charAt = control.SCIGetCharAt(curPos)
    braceAtPos = braceOpposite = -1
    if charBefore in "[](){}":
        braceAtPos = curPos - 1
    if braceAtPos == -1:
        if charAt in "[](){}":
            braceAtPos = curPos
    if braceAtPos != -1:
        braceOpposite = control.SCIBraceMatch(braceAtPos, 0)
    if braceAtPos != -1 and braceOpposite == -1:
        control.SCIBraceBadHighlight(braceAtPos)
    else:
        # 038914.python.view.line125.comment either clear them both or set them both.
        control.SCIBraceHighlight(braceAtPos, braceOpposite)


def _get_class_attributes(ob):
    # 038915.python.view.line130.comment Recurse into base classes looking for attributes
    items = []
    try:
        items.extend(dir(ob))
        for i in ob.__bases__:
            for item in _get_class_attributes(i):
                if item not in items:
                    items.append(item)
    except AttributeError:
        pass
    return items


# 038916.python.view.line143.comment Supposed to look like an MFC CEditView, but
# 038917.python.view.line144.comment also supports IDLE extensions and other source code generic features.
class CScintillaView(docview.CtrlView, control.CScintillaColorEditInterface):
    def __init__(self, doc):
        docview.CtrlView.__init__(
            self,
            doc,
            "Scintilla",
            win32con.WS_CHILD
            | win32con.WS_VSCROLL
            | win32con.WS_HSCROLL
            | win32con.WS_CLIPCHILDREN
            | win32con.WS_VISIBLE,
        )
        self._tabWidth = (
            8  # Mirror of what we send to Scintilla - never change this directly
        )
        self.bAutoCompleteAttributes = 1
        self.bShowCallTips = 1
        self.bMatchBraces = 0  # Editor option will default this to true later!
        self.bindings = bindings.BindingsManager(self)

        self.idle = IDLEenvironment.IDLEEditorWindow(self)
        self.idle.IDLEExtension("AutoExpand")
        # 038920.python.view.line167.comment SendScintilla is called so frequently it is worth optimizing.
        self.SendScintilla = self._obj_.SendMessage

    def _MakeColorizer(self):
        ext = os.path.splitext(self.GetDocument().GetPathName())[1]
        from . import formatter

        return formatter.BuiltinPythonSourceFormatter(self, ext)

    # 038921.python.view.line176.comment def SendScintilla(self, msg, w=0, l=0):
    # 038922.python.view.line177.comment return self._obj_.SendMessage(msg, w, l)

    def SCISetTabWidth(self, width):
        # 038923.python.view.line180.comment I need to remember the tab-width for the AutoIndent extension.  This may go.
        self._tabWidth = width
        control.CScintillaEditInterface.SCISetTabWidth(self, width)

    def GetTabWidth(self):
        return self._tabWidth

    def HookHandlers(self):
        # 038924.python.view.line188.comment Create events for all the menu names.
        for name, val in event_commands:
            # 038925.python.view.line190.comment handler = lambda id, code, tosend=val, parent=parent: parent.OnCommand(tosend, 0) and 0
            self.bindings.bind(name, None, cid=val)

        # 038926.python.view.line193.comment Hook commands that do nothing other than send Scintilla messages.
        for command, reflection in command_reflectors:
            handler = (
                lambda id, code, ss=self.SendScintilla, tosend=reflection: ss(tosend)
                and 0
            )
            self.HookCommand(handler, command)

        self.HookCommand(self.OnCmdViewWS, win32ui.ID_VIEW_WHITESPACE)
        self.HookCommandUpdate(self.OnUpdateViewWS, win32ui.ID_VIEW_WHITESPACE)
        self.HookCommand(
            self.OnCmdViewIndentationGuides, win32ui.ID_VIEW_INDENTATIONGUIDES
        )
        self.HookCommandUpdate(
            self.OnUpdateViewIndentationGuides, win32ui.ID_VIEW_INDENTATIONGUIDES
        )
        self.HookCommand(self.OnCmdViewRightEdge, win32ui.ID_VIEW_RIGHT_EDGE)
        self.HookCommandUpdate(self.OnUpdateViewRightEdge, win32ui.ID_VIEW_RIGHT_EDGE)
        self.HookCommand(self.OnCmdViewEOL, win32ui.ID_VIEW_EOL)
        self.HookCommandUpdate(self.OnUpdateViewEOL, win32ui.ID_VIEW_EOL)
        self.HookCommand(self.OnCmdViewFixedFont, win32ui.ID_VIEW_FIXED_FONT)
        self.HookCommandUpdate(self.OnUpdateViewFixedFont, win32ui.ID_VIEW_FIXED_FONT)
        self.HookCommand(self.OnCmdFileLocate, win32ui.ID_FILE_LOCATE)
        self.HookCommand(self.OnCmdEditFind, win32ui.ID_EDIT_FIND)
        self.HookCommand(self.OnCmdEditRepeat, win32ui.ID_EDIT_REPEAT)
        self.HookCommand(self.OnCmdEditReplace, win32ui.ID_EDIT_REPLACE)
        self.HookCommand(self.OnCmdGotoLine, win32ui.ID_EDIT_GOTO_LINE)
        self.HookCommand(self.OnFilePrint, afxres.ID_FILE_PRINT)
        self.HookCommand(self.OnFilePrint, afxres.ID_FILE_PRINT_DIRECT)
        self.HookCommand(self.OnFilePrintPreview, win32ui.ID_FILE_PRINT_PREVIEW)
        # 038927.python.view.line223.comment Key bindings.
        self.HookMessage(self.OnKeyDown, win32con.WM_KEYDOWN)
        self.HookMessage(self.OnKeyDown, win32con.WM_SYSKEYDOWN)
        # 038928.python.view.line226.comment Hook wheeley mouse events
        # 038929.python.view.line227.comment self.HookMessage(self.OnMouseWheel, win32con.WM_MOUSEWHEEL)
        self.HookFormatter()

    def OnInitialUpdate(self):
        doc = self.GetDocument()

        # 038930.python.view.line233.comment Enable Unicode
        self.SendScintilla(scintillacon.SCI_SETCODEPAGE, scintillacon.SC_CP_UTF8, 0)
        self.SendScintilla(scintillacon.SCI_SETKEYSUNICODE, 1, 0)

        # 038931.python.view.line237.comment Create margins
        self.SendScintilla(
            scintillacon.SCI_SETMARGINTYPEN, 1, scintillacon.SC_MARGIN_SYMBOL
        )
        self.SendScintilla(scintillacon.SCI_SETMARGINMASKN, 1, 0xF)
        self.SendScintilla(
            scintillacon.SCI_SETMARGINTYPEN, 2, scintillacon.SC_MARGIN_SYMBOL
        )
        self.SendScintilla(
            scintillacon.SCI_SETMARGINMASKN, 2, scintillacon.SC_MASK_FOLDERS
        )
        self.SendScintilla(scintillacon.SCI_SETMARGINSENSITIVEN, 2, 1)

        self.GetDocument().HookViewNotifications(
            self
        )  # is there an MFC way to grab this?
        self.HookHandlers()

        # 038933.python.view.line255.comment Load the configuration information.
        self.OnWinIniChange(None)

        self.SetSel()

        self.GetDocument().FinalizeViewCreation(
            self
        )  # is there an MFC way to grab this?

    def _GetSubConfigNames(self):
        return None  # By default we use only sections without sub-sections.

    def OnWinIniChange(self, section=None):
        self.bindings.prepare_configure()
        try:
            self.DoConfigChange()
        finally:
            self.bindings.complete_configure()

    def DoConfigChange(self):
        # 038936.python.view.line275.comment Bit of a hack I don't kow what to do about - these should be "editor options"
        from pywin.framework.editor import GetEditorOption

        self.bAutoCompleteAttributes = GetEditorOption("Autocomplete Attributes", 1)
        self.bShowCallTips = GetEditorOption("Show Call Tips", 1)
        # 038937.python.view.line280.comment Update the key map and extension data.
        configManager.configure(self, self._GetSubConfigNames())
        if configManager.last_error:
            win32ui.MessageBox(configManager.last_error, "Configuration Error")
        self.bMatchBraces = GetEditorOption("Match Braces", 1)
        self.ApplyFormattingStyles(1)

    def OnDestroy(self, msg):
        self.bindings.close()
        self.bindings = None
        self.idle.close()
        self.idle = None
        control.CScintillaColorEditInterface.close(self)
        return docview.CtrlView.OnDestroy(self, msg)

    def OnMouseWheel(self, msg):
        zDelta = msg[2] >> 16
        vpos = self.GetScrollPos(win32con.SB_VERT)
        vpos -= zDelta / 40  # 3 lines per notch
        self.SetScrollPos(win32con.SB_VERT, vpos)
        self.SendScintilla(
            win32con.WM_VSCROLL, (vpos << 16) | win32con.SB_THUMBPOSITION, 0
        )

    def OnBraceMatch(self, std, extra):
        if not self.bMatchBraces:
            return
        DoBraceMatch(self)

    def OnNeedShown(self, std, extra):
        notify = self.SCIUnpackNotifyMessage(extra)
        # 038939.python.view.line311.comment OnNeedShown is called before an edit operation when
        # 038940.python.view.line312.comment text is folded (as it is possible the text insertion will happen
        # 038941.python.view.line313.comment in a folded region.)  As this happens _before_ the insert,
        # 038942.python.view.line314.comment we ignore the length (if we are at EOF, pos + length may
        # 038943.python.view.line315.comment actually be beyond the end of buffer)
        self.EnsureCharsVisible(notify.position)

    def EnsureCharsVisible(self, start, end=None):
        if end is None:
            end = start
        lineStart = self.LineFromChar(min(start, end))
        lineEnd = self.LineFromChar(max(start, end))
        while lineStart <= lineEnd:
            self.SCIEnsureVisible(lineStart)
            lineStart += 1

    # 038944.python.view.line327.comment Helper to add an event to a menu.
    def AppendMenu(self, menu, text="", event=None, flags=None, checked=0):
        if event is None:
            assert flags is not None, "No event or custom flags!"
            cmdid = 0
        else:
            cmdid = self.bindings.get_command_id(event)
            if cmdid is None:
                # 038945.python.view.line335.comment No event of that name - no point displaying it.
                print(
                    'View.AppendMenu(): Unknown event "{}" specified for menu text "{}" - ignored'.format(
                        event, text
                    )
                )
                return
            keyname = configManager.get_key_binding(event, self._GetSubConfigNames())
            if keyname is not None:
                text += "\t" + keyname
        if flags is None:
            flags = win32con.MF_STRING | win32con.MF_ENABLED
        if checked:
            flags |= win32con.MF_CHECKED
        menu.AppendMenu(flags, cmdid, text)

    def OnKeyDown(self, msg):
        return self.bindings.fire_key_event(msg)

    def GotoEndOfFileEvent(self, event):
        self.SetSel(-1)

    def KeyDotEvent(self, event):
        # 038946.python.view.line358.comment # Don't trigger autocomplete if any text is selected
        s, e = self.GetSel()
        if s != e:
            return 1
        self.SCIAddText(".")
        if self.bAutoCompleteAttributes:
            self._AutoComplete()

    # 038947.python.view.line366.comment View Whitespace/EOL/Indentation UI.

    def OnCmdViewWS(self, cmd, code):  # Handle the menu command
        viewWS = self.SCIGetViewWS()
        self.SCISetViewWS(not viewWS)

    def OnUpdateViewWS(self, cmdui):  # Update the tick on the UI.
        cmdui.SetCheck(self.SCIGetViewWS())
        cmdui.Enable()

    def OnCmdViewIndentationGuides(self, cmd, code):  # Handle the menu command
        viewIG = self.SCIGetIndentationGuides()
        self.SCISetIndentationGuides(not viewIG)

    def OnUpdateViewIndentationGuides(self, cmdui):  # Update the tick on the UI.
        cmdui.SetCheck(self.SCIGetIndentationGuides())
        cmdui.Enable()

    def OnCmdViewRightEdge(self, cmd, code):  # Handle the menu command
        if self.SCIGetEdgeMode() == scintillacon.EDGE_NONE:
            mode = scintillacon.EDGE_BACKGROUND
        else:
            mode = scintillacon.EDGE_NONE
        self.SCISetEdgeMode(mode)

    def OnUpdateViewRightEdge(self, cmdui):  # Update the tick on the UI.
        cmdui.SetCheck(self.SCIGetEdgeMode() != scintillacon.EDGE_NONE)
        cmdui.Enable()

    def OnCmdViewEOL(self, cmd, code):  # Handle the menu command
        viewEOL = self.SCIGetViewEOL()
        self.SCISetViewEOL(not viewEOL)

    def OnUpdateViewEOL(self, cmdui):  # Update the tick on the UI.
        cmdui.SetCheck(self.SCIGetViewEOL())
        cmdui.Enable()

    def OnCmdViewFixedFont(self, cmd, code):  # Handle the menu command
        self._GetColorizer().bUseFixed = not self._GetColorizer().bUseFixed
        self.ApplyFormattingStyles(0)
        # 038957.python.view.line406.comment Ensure the selection is visible!
        self.ScrollCaret()

    def OnUpdateViewFixedFont(self, cmdui):  # Update the tick on the UI.
        c = self._GetColorizer()
        if c is not None:
            cmdui.SetCheck(c.bUseFixed)
        cmdui.Enable(c is not None)

    def OnCmdEditFind(self, cmd, code):
        from . import find

        find.ShowFindDialog()

    def OnCmdEditRepeat(self, cmd, code):
        from . import find

        find.FindNext()

    def OnCmdEditReplace(self, cmd, code):
        from . import find

        find.ShowReplaceDialog()

    def OnCmdFileLocate(self, cmd, id):
        line = self.GetLine().strip()
        import pywin.framework.scriptutils

        m = patImport.match(line)
        if m:
            # 038959.python.view.line436.comment Module name on this line - locate that!
            modName = m.group("name")
            fileName = pywin.framework.scriptutils.LocatePythonFile(modName)
            if fileName is None:
                win32ui.SetStatusText("Can't locate module %s" % modName)
                return 1  # Let the default get it.
            else:
                win32ui.GetApp().OpenDocumentFile(fileName)
        else:
            # 038961.python.view.line445.comment Just to a "normal" locate - let the default handler get it.
            return 1
        return 0

    def OnCmdGotoLine(self, cmd, id):
        try:
            lineNo = int(input("Enter Line Number")) - 1
        except (ValueError, KeyboardInterrupt):
            return 0
        self.SCIEnsureVisible(lineNo)
        self.SCIGotoLine(lineNo)
        return 0

    def SaveTextFile(self, filename, encoding=None):
        doc = self.GetDocument()
        doc._SaveTextToFile(self, filename, encoding=encoding)
        doc.SetModifiedFlag(0)
        return 1

    def _AutoComplete(self):
        self.SCIAutoCCancel()  # Cancel old auto-complete lists.
        # 038963.python.view.line466.comment First try and get an object without evaluating calls
        ob = self._GetObjectAtPos(bAllowCalls=0)
        # 038964.python.view.line468.comment If that failed, try and process call or indexing to get the object.
        if ob is None:
            ob = self._GetObjectAtPos(bAllowCalls=1)
        items_dict = {}
        if ob is not None:
            try:  # Catch unexpected errors when fetching attribute names from the object
                # 038966.python.view.line474.comment extra attributes of win32ui objects
                if hasattr(ob, "_obj_"):
                    try:
                        items_dict.update(dict.fromkeys(dir(ob._obj_)))
                    except AttributeError:
                        pass  # object has no __dict__

                # 038968.python.view.line481.comment normal attributes
                try:
                    items_dict.update(dict.fromkeys(dir(ob)))
                except AttributeError:
                    pass  # object has no __dict__
                if hasattr(ob, "__class__"):
                    items_dict.update(
                        dict.fromkeys(_get_class_attributes(ob.__class__))
                    )
                # 038970.python.view.line490.comment The object may be a COM object with typelib support - let's see if we can get its props.
                # 038971.python.view.line491.comment (contributed by Stefan Migowsky)
                try:
                    # 038972.python.view.line493.comment Get the automation attributes
                    items_dict.update(ob.__class__._prop_map_get_)
                    # 038973.python.view.line495.comment See if there is an write only property
                    # 038974.python.view.line496.comment could be optimized
                    items_dict.update(ob.__class__._prop_map_put_)
                    # 038975.python.view.line498.comment append to the already evaluated list
                except AttributeError:
                    pass
                # 038976.python.view.line501.comment The object might be a pure COM dynamic dispatch with typelib support - let's see if we can get its props.
                if hasattr(ob, "_oleobj_"):
                    try:
                        for iTI in range(0, ob._oleobj_.GetTypeInfoCount()):
                            typeInfo = ob._oleobj_.GetTypeInfo(iTI)
                            self._UpdateWithITypeInfo(items_dict, typeInfo)
                    except:
                        pass
            except:
                win32ui.SetStatusText(
                    f"Error attempting to get object attributes - {sys.exc_info()[0]!r}"
                )

        items = [
            k
            for k in
            # 038977.python.view.line517.comment ensure all keys are strings.
            map(str, items_dict)
            # 038978.python.view.line519.comment All names that start with "_" go!
            if not k.startswith("_")
        ]

        if not items:
            # 038979.python.view.line524.comment Heuristics a-la AutoExpand
            # 038980.python.view.line525.comment The idea is to find other usages of the current binding
            # 038981.python.view.line526.comment and assume, that it refers to the same object (or at least,
            # 038982.python.view.line527.comment to an object of the same type)
            # 038983.python.view.line528.comment Contributed by Vadim Chugunov [vadimch@yahoo.com]
            left, right = self._GetWordSplit()
            if left == "":  # Ignore standalone dots
                return None
            # 038985.python.view.line532.comment We limit our search to the current class, if that
            # 038986.python.view.line533.comment information is available
            minline, maxline, curclass = self._GetClassInfoFromBrowser()
            endpos = self.LineIndex(maxline)
            text = self.GetTextRange(self.LineIndex(minline), endpos)
            try:
                l = re.findall(r"\b" + left + r"\.\w+", text)
            except re.error:
                # 038987.python.view.line540.comment parens etc may make an invalid RE, but this code wouldnt
                # 038988.python.view.line541.comment benefit even if the RE did work :-)
                l = []
            prefix = len(left) + 1
            unique = {}
            for li in l:
                unique[li[prefix:]] = 1
            # 038989.python.view.line547.comment Assuming traditional usage of self...
            if curclass and left == "self":
                self._UpdateWithClassMethods(unique, curclass)

            items = [word for word in unique if word[:2] != "__" or word[-2:] != "__"]
            # 038990.python.view.line552.comment Ignore the word currently to the right of the dot - probably a red-herring.
            try:
                items.remove(right[1:])
            except ValueError:
                pass
        if items:
            items.sort()
            self.SCIAutoCSetAutoHide(0)
            self.SCIAutoCShow(items)

    def _UpdateWithITypeInfo(self, items_dict, typeInfo):
        import pythoncom

        typeInfos = [typeInfo]
        # 038991.python.view.line566.comment suppress IDispatch and IUnknown methods
        inspectedIIDs = {pythoncom.IID_IDispatch: None}

        while len(typeInfos) > 0:
            typeInfo = typeInfos.pop()
            typeAttr = typeInfo.GetTypeAttr()

            if typeAttr.iid not in inspectedIIDs:
                inspectedIIDs[typeAttr.iid] = None
                for iFun in range(0, typeAttr.cFuncs):
                    funDesc = typeInfo.GetFuncDesc(iFun)
                    funName = typeInfo.GetNames(funDesc.memid)[0]
                    if funName not in items_dict:
                        items_dict[funName] = None

                # 038992.python.view.line581.comment Inspect the type info of all implemented types
                # 038993.python.view.line582.comment E.g. IShellDispatch5 implements IShellDispatch4 which implements IShellDispatch3 ...
                for iImplType in range(0, typeAttr.cImplTypes):
                    iRefType = typeInfo.GetRefTypeOfImplType(iImplType)
                    refTypeInfo = typeInfo.GetRefTypeInfo(iRefType)
                    typeInfos.append(refTypeInfo)

    # 038994.python.view.line588.comment TODO: This is kinda slow. Probably need some kind of cache
    # 038995.python.view.line589.comment here that is flushed upon file save
    # 038996.python.view.line590.comment Or maybe we don't need the superclass methods at all ?
    def _UpdateWithClassMethods(self, dict, classinfo):
        if not hasattr(classinfo, "methods"):
            # 038997.python.view.line593.comment No 'methods' - probably not what we think it is.
            return
        dict.update(classinfo.methods)
        for super in classinfo.super:
            if hasattr(super, "methods"):
                self._UpdateWithClassMethods(dict, super)

    # 038998.python.view.line600.comment Find which class definition caret is currently in and return
    # 038999.python.view.line601.comment indexes of the the first and the last lines of that class definition
    # 039000.python.view.line602.comment Data is obtained from module browser (if enabled)
    def _GetClassInfoFromBrowser(self, pos=-1):
        minline = 0
        maxline = self.GetLineCount() - 1
        doc = self.GetParentFrame().GetActiveDocument()
        browser = None
        try:
            if doc is not None:
                browser = doc.GetAllViews()[1]
        except IndexError:
            pass
        if browser is None:
            return (minline, maxline, None)  # Current window has no browser
        if not browser.list:
            return (minline, maxline, None)  # Not initialized
        path = self.GetDocument().GetPathName()
        if not path:
            return (minline, maxline, None)  # No current path

        import pywin.framework.scriptutils

        curmodule, path = pywin.framework.scriptutils.GetPackageModuleName(path)
        try:
            clbrdata = browser.list.root.clbrdata
        except AttributeError:
            return (minline, maxline, None)  # No class data for this module.
        curline = self.LineFromChar(pos)
        curclass = None
        # 039005.python.view.line630.comment Find out which class we are in
        for item in clbrdata.values():
            if item.module == curmodule:
                item_lineno = (
                    item.lineno - 1
                )  # Scintilla counts lines from 0, whereas pyclbr - from 1
                if minline < item_lineno <= curline:
                    minline = item_lineno
                    curclass = item
                if curline < item_lineno < maxline:
                    maxline = item_lineno
        return (minline, maxline, curclass)

    def _GetObjectAtPos(self, pos=-1, bAllowCalls=0):
        left, right = self._GetWordSplit(pos, bAllowCalls)
        if left:  # It is an attribute lookup
            # 039008.python.view.line646.comment How is this for a hack!
            namespace = sys.modules.copy()
            namespace.update(__main__.__dict__)
            # 039009.python.view.line649.comment Get the debugger's context.
            try:
                from pywin.framework import interact

                if interact.edit is not None and interact.edit.currentView is not None:
                    globs, locs = interact.edit.currentView.GetContext()[:2]
                    if globs:
                        namespace.update(globs)
                    if locs:
                        namespace.update(locs)
            except ImportError:
                pass
            try:
                return eval(left, namespace)
            except:
                pass
        return None

    def _GetWordSplit(self, pos=-1, bAllowCalls=0):
        if pos == -1:
            pos = self.GetSel()[0] - 1  # Character before current one
        limit = self.GetTextLength()
        before = []
        after = []
        index = pos - 1
        wordbreaks_use = wordbreaks
        if bAllowCalls:
            wordbreaks_use += "()[]"
        while index >= 0:
            char = self.SCIGetCharAt(index)
            if char not in wordbreaks_use:
                break
            before.insert(0, char)
            index -= 1
        index = pos
        while index <= limit:
            char = self.SCIGetCharAt(index)
            if char not in wordbreaks_use:
                break
            after.append(char)
            index += 1
        return "".join(before), "".join(after)

    def OnPrepareDC(self, dc, pInfo):
        # 039011.python.view.line693.comment print(
        # 039012.python.view.line694.comment "OnPrepareDC for page",
        # 039013.python.view.line695.comment pInfo.GetCurPage(),
        # 039014.python.view.line696.comment "of",
        # 039015.python.view.line697.comment pInfo.GetFromPage(),
        # 039016.python.view.line698.comment "to",
        # 039017.python.view.line699.comment pInfo.GetToPage(),
        # 039018.python.view.line700.comment ", starts=",
        # 039019.python.view.line701.comment self.starts,
        # 039020.python.view.line702.comment )
        if dc.IsPrinting():
            # 039021.python.view.line704.comment Check if we are beyond the end.
            # 039022.python.view.line705.comment (only do this when actually printing, else messes up print preview!)
            if not pInfo.GetPreview() and self.starts is not None:
                prevPage = pInfo.GetCurPage() - 1
                if prevPage > 0 and self.starts[prevPage] >= self.GetTextLength():
                    # 039023.python.view.line709.comment All finished.
                    pInfo.SetContinuePrinting(0)
                    return
            dc.SetMapMode(win32con.MM_TEXT)

    def OnPreparePrinting(self, pInfo):
        flags = (
            win32ui.PD_USEDEVMODECOPIES | win32ui.PD_ALLPAGES | win32ui.PD_NOSELECTION
        )  # Don't support printing just a selection.
        # 039025.python.view.line718.comment NOTE: Custom print dialogs are stopping the user's values from coming back :-(
        # 039026.python.view.line719.comment self.prtDlg = PrintDialog(pInfo, PRINTDLGORD, flags)
        # 039027.python.view.line720.comment pInfo.SetPrintDialog(self.prtDlg)
        pInfo.SetMinPage(1)
        # 039028.python.view.line722.comment max page remains undefined for now.
        pInfo.SetFromPage(1)
        pInfo.SetToPage(1)
        ret = self.DoPreparePrinting(pInfo)
        return ret

    def OnBeginPrinting(self, dc, pInfo):
        self.starts = None
        return self._obj_.OnBeginPrinting(dc, pInfo)

    def CalculatePageRanges(self, dc, pInfo):
        # 039029.python.view.line733.comment Calculate page ranges and max page
        self.starts = {0: 0}
        metrics = dc.GetTextMetrics()
        left, top, right, bottom = pInfo.GetDraw()
        # 039030.python.view.line737.comment Leave space at the top for the header.
        rc = (left, top + int((9 * metrics["tmHeight"]) / 2), right, bottom)
        pageStart = 0
        maxPage = 0
        textLen = self.GetTextLength()
        while pageStart < textLen:
            pageStart = self.FormatRange(dc, pageStart, textLen, rc, 0)
            maxPage += 1
            self.starts[maxPage] = pageStart
        # 039031.python.view.line746.comment And a sentinel for one page past the end
        self.starts[maxPage + 1] = textLen
        # 039032.python.view.line748.comment When actually printing, maxPage doesn't have any effect at this late state.
        # 039033.python.view.line749.comment but is needed to make the Print Preview work correctly.
        pInfo.SetMaxPage(maxPage)

    def OnFilePrintPreview(self, *arg):
        self._obj_.OnFilePrintPreview()

    def OnFilePrint(self, *arg):
        self._obj_.OnFilePrint()

    def FormatRange(self, dc, pageStart, lengthDoc, rc, draw):
        """
        typedef struct _formatrange {
                HDC hdc;
                HDC hdcTarget;
                RECT rc;
                RECT rcPage;
                CHARRANGE chrg;} FORMATRANGE;
        """
        fmt = "PPIIIIIIIIll"
        hdcRender = dc.GetHandleOutput()
        hdcFormat = dc.GetHandleAttrib()
        fr = struct.pack(
            fmt,
            hdcRender,
            hdcFormat,
            rc[0],
            rc[1],
            rc[2],
            rc[3],
            rc[0],
            rc[1],
            rc[2],
            rc[3],
            pageStart,
            lengthDoc,
        )
        nextPageStart = self.SendScintilla(EM_FORMATRANGE, draw, fr)
        return nextPageStart

    def OnPrint(self, dc, pInfo):
        metrics = dc.GetTextMetrics()
        # 039034.python.view.line790.comment print("dev", w, h, l, metrics["tmAscent"], metrics["tmDescent"])
        if self.starts is None:
            self.CalculatePageRanges(dc, pInfo)
        pageNum = pInfo.GetCurPage() - 1
        # 039035.python.view.line794.comment Setup the header of the page - docname on left, pagenum on right.
        doc = self.GetDocument()
        cxChar = metrics["tmAveCharWidth"]
        cyChar = metrics["tmHeight"]
        left, top, right, bottom = pInfo.GetDraw()
        dc.TextOut(0, 2 * cyChar, doc.GetTitle())
        pagenum_str = win32ui.LoadString(afxres.AFX_IDS_PRINTPAGENUM) % (pageNum + 1,)
        dc.SetTextAlign(win32con.TA_RIGHT)
        dc.TextOut(right, 2 * cyChar, pagenum_str)
        dc.SetTextAlign(win32con.TA_LEFT)
        top += int(7 * cyChar / 2)
        dc.MoveTo(left, top)
        dc.LineTo(right, top)
        top += cyChar
        rc = (left, top, right, bottom)
        nextPageStart = self.FormatRange(
            dc, self.starts[pageNum], self.starts[pageNum + 1], rc, 1
        )


def LoadConfiguration():
    global configManager
    # 039036.python.view.line816.comment Bit of a hack I don't kow what to do about?
    from .config import ConfigManager

    configName = rc = win32ui.GetProfileVal("Editor", "Keyboard Config", "default")
    configManager = ConfigManager(configName)
    if configManager.last_error:
        bTryDefault = 0
        msg = "Error loading configuration '{}'\n\n{}".format(
            configName,
            configManager.last_error,
        )
        if configName != "default":
            msg += "\n\nThe default configuration will be loaded."
            bTryDefault = 1
        win32ui.MessageBox(msg)
        if bTryDefault:
            configManager = ConfigManager("default")
            if configManager.last_error:
                win32ui.MessageBox(
                    "Error loading configuration 'default'\n\n%s"
                    % (configManager.last_error)
                )


configManager = None
LoadConfiguration()
