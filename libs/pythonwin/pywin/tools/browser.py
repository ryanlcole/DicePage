# 039062.python.browser.line1.comment basic module browser.

# 039063.python.browser.line3.comment usage:
# 039064.python.browser.line4.comment >>> import browser
# 039065.python.browser.line5.comment >>> browser.Browse()
# 039066.python.browser.line6.comment or
# 039067.python.browser.line7.comment >>> browser.Browse(your_module)
import sys
import types

import __main__
import win32ui
from pywin.mfc import dialog

from . import hierlist

special_names = ["__doc__", "__name__", "__self__"]


# 039068.python.browser.line20.comment
# 039069.python.browser.line21.comment HierList items
class HLIPythonObject(hierlist.HierListItem):
    def __init__(self, myobject=None, name=None):
        hierlist.HierListItem.__init__(self)
        self.myobject = myobject
        self.knownExpandable = None
        if name:
            self.name = name
        else:
            try:
                self.name = myobject.__name__
            except (AttributeError, TypeError):
                try:
                    r = repr(myobject)
                    if len(r) > 20:
                        r = r[:20] + "..."
                    self.name = r
                except (AttributeError, TypeError):
                    self.name = "???"

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(name={self.name!r}, object={self.myobject!r})"
        )

    def GetText(self):
        try:
            return f"{self.name} ({self.GetHLIType()})"
        except AttributeError:
            return f"{self.name} = {self.myobject!r}"

    def InsertDocString(self, lst):
        ob = None
        try:
            ob = self.myobject.__doc__
        except (AttributeError, TypeError):
            pass
        # 039070.python.browser.line64.comment I don't quite grok descriptors enough to know how to
        # 039071.python.browser.line65.comment best hook them up. Eg:
        # 039072.python.browser.line66.comment >>> object.__getattribute__.__class__.__doc__
        # 039073.python.browser.line67.comment <attribute '__doc__' of 'wrapper_descriptor' objects>
        if ob and isinstance(ob, str):
            lst.insert(0, HLIDocString(ob, "Doc"))

    def GetSubList(self):
        ret = []
        try:
            for key, ob in self.myobject.__dict__.items():
                if key not in special_names:
                    ret.append(MakeHLI(ob, key))
        except (AttributeError, TypeError):
            pass
        try:
            for name in self.myobject.__methods__:
                ret.append(HLIMethod(name))  # no MakeHLI, as can't auto detect
        except (AttributeError, TypeError):
            pass
        try:
            for member in self.myobject.__members__:
                if not member in special_names:
                    ret.append(MakeHLI(getattr(self.myobject, member), member))
        except (AttributeError, TypeError):
            pass
        ret.sort()
        self.InsertDocString(ret)
        return ret

    # 039075.python.browser.line94.comment if the has a dict, it is expandable.
    def IsExpandable(self):
        if self.knownExpandable is None:
            self.knownExpandable = self.CalculateIsExpandable()
        return self.knownExpandable

    def CalculateIsExpandable(self):
        if hasattr(self.myobject, "__doc__"):
            return 1
        try:
            for key in self.myobject.__dict__:
                if key not in special_names:
                    return 1
        except (AttributeError, TypeError):
            pass
        try:
            self.myobject.__methods__
            return 1
        except (AttributeError, TypeError):
            pass
        try:
            for item in self.myobject.__members__:
                if item not in special_names:
                    return 1
        except (AttributeError, TypeError):
            pass
        return 0

    def GetBitmapColumn(self):
        if self.IsExpandable():
            return 0
        else:
            return 4

    def TakeDefaultAction(self):
        ShowObject(self.myobject, self.name)


class HLIDocString(HLIPythonObject):
    def GetHLIType(self):
        return "DocString"

    def GetText(self):
        return self.myobject.strip()

    def IsExpandable(self):
        return 0

    def GetBitmapColumn(self):
        return 6


class HLIModule(HLIPythonObject):
    def GetHLIType(self):
        return "Module"


class HLIFrame(HLIPythonObject):
    def GetHLIType(self):
        return "Stack Frame"


class HLITraceback(HLIPythonObject):
    def GetHLIType(self):
        return "Traceback"


class HLIClass(HLIPythonObject):
    def GetHLIType(self):
        return "Class"

    def GetSubList(self):
        ret = []
        for base in self.myobject.__bases__:
            ret.append(MakeHLI(base, "Base class: " + base.__name__))
        ret.extend(HLIPythonObject.GetSubList(self))
        return ret


class HLIMethod(HLIPythonObject):
    # 039076.python.browser.line174.comment myobject is just a string for methods.
    def GetHLIType(self):
        return "Method"

    def GetText(self):
        return "Method: " + self.myobject + "()"


class HLICode(HLIPythonObject):
    def GetHLIType(self):
        return "Code"

    def IsExpandable(self):
        return self.myobject

    def GetSubList(self):
        ret = []
        ret.append(MakeHLI(self.myobject.co_consts, "Constants (co_consts)"))
        ret.append(MakeHLI(self.myobject.co_names, "Names (co_names)"))
        ret.append(MakeHLI(self.myobject.co_filename, "Filename (co_filename)"))
        ret.append(MakeHLI(self.myobject.co_argcount, "Number of args (co_argcount)"))
        ret.append(MakeHLI(self.myobject.co_varnames, "Param names (co_varnames)"))

        return ret


class HLIInstance(HLIPythonObject):
    def GetHLIType(self):
        return "Instance"

    def GetText(self):
        return (
            str(self.name)
            + " (Instance of class "
            + str(self.myobject.__class__.__name__)
            + ")"
        )

    def IsExpandable(self):
        return 1

    def GetSubList(self):
        ret = []
        ret.append(MakeHLI(self.myobject.__class__))
        ret.extend(HLIPythonObject.GetSubList(self))
        return ret


class HLIBuiltinFunction(HLIPythonObject):
    def GetHLIType(self):
        return "Builtin Function"


class HLIFunction(HLIPythonObject):
    def GetHLIType(self):
        return "Function"

    def IsExpandable(self):
        return 1

    def GetSubList(self):
        ret = [
            MakeHLI(self.myobject.__code__, "Code"),
            MakeHLI(self.myobject.__globals__, "Globals"),
        ]
        self.InsertDocString(ret)
        return ret


class HLISeq(HLIPythonObject):
    def GetHLIType(self):
        return "Sequence (abstract!)"

    def IsExpandable(self):
        return len(self.myobject) > 0

    def GetSubList(self):
        ret = []
        pos = 0
        for item in self.myobject:
            ret.append(MakeHLI(item, f"[{pos}]"))
            pos += 1
        self.InsertDocString(ret)
        return ret


class HLIList(HLISeq):
    def GetHLIType(self):
        return "List"


class HLITuple(HLISeq):
    def GetHLIType(self):
        return "Tuple"


class HLIDict(HLIPythonObject):
    def GetHLIType(self):
        return "Dict"

    def IsExpandable(self):
        try:
            self.myobject.__doc__
            return 1
        except (AttributeError, TypeError):
            return len(self.myobject) > 0

    def GetSubList(self):
        ret = [MakeHLI(self.myobject[key], str(key)) for key in sorted(self.myobject)]
        self.InsertDocString(ret)
        return ret


# 039077.python.browser.line287.comment strings and Unicode have builtin methods, but we don't really want to see these
class HLIString(HLIPythonObject):
    def IsExpandable(self):
        return 0


TypeMap = {
    type: HLIClass,
    types.FunctionType: HLIFunction,
    tuple: HLITuple,
    dict: HLIDict,
    list: HLIList,
    types.ModuleType: HLIModule,
    types.CodeType: HLICode,
    types.BuiltinFunctionType: HLIBuiltinFunction,
    types.FrameType: HLIFrame,
    types.TracebackType: HLITraceback,
    str: HLIString,
    int: HLIPythonObject,
    bool: HLIPythonObject,
    float: HLIPythonObject,
}


def MakeHLI(ob, name=None):
    try:
        cls = TypeMap[type(ob)]
    except KeyError:
        # 039078.python.browser.line315.comment hrmph - this check gets more and more bogus as Python
        # 039079.python.browser.line316.comment improves.  It's possible we should just *always* use
        # 039080.python.browser.line317.comment HLIInstance?
        if hasattr(ob, "__class__"):  # 'new style' class
            cls = HLIInstance
        else:
            cls = HLIPythonObject
    return cls(ob, name)


# 039082.python.browser.line325.comment ########################################
# 039083.python.browser.line326.comment
# 039084.python.browser.line327.comment Dialog related.


class DialogShowObject(dialog.Dialog):
    def __init__(self, object, title):
        self.object = object
        self.title = title
        dialog.Dialog.__init__(self, win32ui.IDD_LARGE_EDIT)

    def OnInitDialog(self):
        import re

        self.SetWindowText(self.title)
        self.edit = self.GetDlgItem(win32ui.IDC_EDIT1)
        try:
            strval = str(self.object)
        except:
            t, v, tb = sys.exc_info()
            strval = f"Exception getting object value\n\n{t}:{v}"
            tb = None
        strval = re.sub(r"\n", "\r\n", strval)
        self.edit.ReplaceSel(strval)


def ShowObject(object, title):
    dlg = DialogShowObject(object, title)
    dlg.DoModal()


# 039085.python.browser.line356.comment And some mods for a sizable dialog from Sam Rushing!
import commctrl
import win32api
import win32con


class dynamic_browser(dialog.Dialog):
    style = win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE
    cs = (
        win32con.WS_CHILD
        | win32con.WS_VISIBLE
        | commctrl.TVS_HASLINES
        | commctrl.TVS_LINESATROOT
        | commctrl.TVS_HASBUTTONS
    )

    dt = [
        ["Python Object Browser", (0, 0, 200, 200), style, None, (8, "MS Sans Serif")],
        ["SysTreeView32", None, win32ui.IDC_LIST1, (0, 0, 200, 200), cs],
    ]

    def __init__(self, hli_root):
        dialog.Dialog.__init__(self, self.dt)
        self.hier_list = hierlist.HierListWithItems(hli_root, win32ui.IDB_BROWSER_HIER)
        self.HookMessage(self.on_size, win32con.WM_SIZE)

    def OnInitDialog(self):
        self.hier_list.HierInit(self)
        return dialog.Dialog.OnInitDialog(self)

    def OnOK(self):
        self.hier_list.HierTerm()
        self.hier_list = None
        return self._obj_.OnOK()

    def OnCancel(self):
        self.hier_list.HierTerm()
        self.hier_list = None
        return self._obj_.OnCancel()

    def on_size(self, params):
        lparam = params[3]
        w = win32api.LOWORD(lparam)
        h = win32api.HIWORD(lparam)
        self.GetDlgItem(win32ui.IDC_LIST1).MoveWindow((0, 0, w, h))


def Browse(ob=__main__):
    "Browse the argument, or the main dictionary"
    root = MakeHLI(ob, "root")
    if not root.IsExpandable():
        raise TypeError(
            "Browse() argument must have __dict__ attribute, or be a Browser supported type"
        )

    dlg = dynamic_browser(root)
    dlg.CreateWindow()
    return dlg


# 039086.python.browser.line416.comment
# 039087.python.browser.line417.comment
# 039088.python.browser.line418.comment Classes for using the browser in an MDI window, rather than a dialog
# 039089.python.browser.line419.comment
from pywin.mfc import docview


class BrowserTemplate(docview.DocTemplate):
    def __init__(self):
        docview.DocTemplate.__init__(
            self, win32ui.IDR_PYTHONTYPE, BrowserDocument, None, BrowserView
        )

    def OpenObject(self, root):  # Use this instead of OpenDocumentFile.
        # 039091.python.browser.line430.comment Look for existing open document
        for doc in self.GetDocumentList():
            if doc.root == root:
                doc.GetFirstView().ActivateFrame()
                return doc
        # 039092.python.browser.line435.comment not found - new one.
        doc = BrowserDocument(self, root)
        frame = self.CreateNewFrame(doc)
        doc.OnNewDocument()
        self.InitialUpdateFrame(frame, doc, 1)
        return doc


class BrowserDocument(docview.Document):
    def __init__(self, template, root):
        docview.Document.__init__(self, template)
        self.root = root
        self.SetTitle("Browser: " + root.name)

    def OnOpenDocument(self, name):
        raise TypeError("This template can not open files")
        return 0


class BrowserView(docview.TreeView):
    def OnInitialUpdate(self):
        import commctrl

        rc = self._obj_.OnInitialUpdate()
        list = hierlist.HierListWithItems(
            self.GetDocument().root,
            win32ui.IDB_BROWSER_HIER,
            win32ui.AFX_IDW_PANE_FIRST,
        )
        list.HierInit(self.GetParent())
        list.SetStyle(
            commctrl.TVS_HASLINES | commctrl.TVS_LINESATROOT | commctrl.TVS_HASBUTTONS
        )
        return rc


template = None


def MakeTemplate():
    global template
    if template is None:
        template = (
            BrowserTemplate()
        )  # win32ui.IDR_PYTHONTYPE, BrowserDocument, None, BrowserView)


def BrowseMDI(ob=__main__):
    """Browse an object using an MDI window."""

    MakeTemplate()
    root = MakeHLI(ob, repr(ob))
    if not root.IsExpandable():
        raise TypeError(
            "Browse() argument must have __dict__ attribute, or be a Browser supported type"
        )

    template.OpenObject(root)
