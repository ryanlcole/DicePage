# 051799.python.shell_view.line1.comment A sample shell namespace view

# 051800.python.shell_view.line3.comment To demonstrate:
# 051801.python.shell_view.line4.comment * Execute this script to register the namespace.
# 051802.python.shell_view.line5.comment * Open Windows Explorer, and locate the new "Python Path Shell Browser"
# 051803.python.shell_view.line6.comment folder off "My Computer"
# 051804.python.shell_view.line7.comment * Browse this tree - .py files are shown expandable, with classes and
# 051805.python.shell_view.line8.comment methods selectable.  Selecting a Python file, or a class/method, will
# 051806.python.shell_view.line9.comment display the file using Scintilla.
# 051807.python.shell_view.line10.comment Known problems:
# 051808.python.shell_view.line11.comment * Classes and methods don't have icons - this is a demo, so we keep it small
# 051809.python.shell_view.line12.comment See icon_handler.py for examples of how to work with icons.
# 051810.python.shell_view.line13.comment
# 051811.python.shell_view.line14.comment
# 051812.python.shell_view.line15.comment Notes on PIDLs
# 051813.python.shell_view.line16.comment PIDLS are complicated, but fairly well documented in MSDN.  If you need to
# 051814.python.shell_view.line17.comment do much with these shell extensions, you must understand their concept.
# 051815.python.shell_view.line18.comment Here is a short-course, as it applies to this sample:
# 051816.python.shell_view.line19.comment A PIDL identifies an item, much in the same way that a filename does
# 051817.python.shell_view.line20.comment (however, the shell is not limited to displaying "files").
# 051818.python.shell_view.line21.comment An "ItemID" is a single string, each being an item in the hierarchy.
# 051819.python.shell_view.line22.comment A "PIDL" is a list of these strings.
# 051820.python.shell_view.line23.comment All shell etc functions work with PIDLs, so even in the case where
# 051821.python.shell_view.line24.comment an ItemID is conceptually used, a 1-item list is always used.
# 051822.python.shell_view.line25.comment Conceptually, think of:
# 051823.python.shell_view.line26.comment pidl = pathname.split("\\") # pidl is a list of "parent" items.
# 051824.python.shell_view.line27.comment # each item is a string 'item id', but these are ever used directly
# 051825.python.shell_view.line28.comment As there is no concept of passing a single item, to open a file using only
# 051826.python.shell_view.line29.comment a relative filename, conceptually you would say:
# 051827.python.shell_view.line30.comment open_file([filename]) # Pass a single-itemed relative "PIDL"
# 051828.python.shell_view.line31.comment and continuing the analogy, a "listdir" type function would return a list
# 051829.python.shell_view.line32.comment of single-itemed lists - each list containing the relative PIDL of the child.
# 051830.python.shell_view.line33.comment
# 051831.python.shell_view.line34.comment Each PIDL entry is a binary string, and may contain any character.  For
# 051832.python.shell_view.line35.comment PIDLs not created by you, they can not be interpreted - they are just
# 051833.python.shell_view.line36.comment blobs.  PIDLs created by you (ie, children of your IShellFolder) can
# 051834.python.shell_view.line37.comment store and interpret the string however makes most sense for your application.
# 051835.python.shell_view.line38.comment (but within PIDL rules - they must be persistable, etc)
# 051836.python.shell_view.line39.comment There is no reason that pickled strings, for example, couldn't be used
# 051837.python.shell_view.line40.comment as an EntryID.
# 051838.python.shell_view.line41.comment This application takes a simple approach - each PIDL is a string of form
# 051839.python.shell_view.line42.comment "directory\0directory_name", "file\0file_name" or
# 051840.python.shell_view.line43.comment "object\0file_name\0class_name[.method_name"
# 051841.python.shell_view.line44.comment The first string in each example is literal (ie, the word 'directory',
# 051842.python.shell_view.line45.comment 'file' or 'object', and every other string is variable.  We use '\0' as
# 051843.python.shell_view.line46.comment a field sep just 'cos we can (and 'cos it can't possibly conflict with the
# 051844.python.shell_view.line47.comment string content)

import os
import pyclbr
import sys

import commctrl
import pythoncom
import win32api
import win32con
import win32gui
import win32gui_struct
import winerror
from pywin.scintilla import scintillacon
from win32com.server.exception import COMException
from win32com.server.util import NewEnum, wrap
from win32com.shell import shell, shellcon
from win32com.util import IIDToInterfaceName

# 051845.python.shell_view.line66.comment Set this to 1 to cause debug version to be registered and used.  A debug
# 051846.python.shell_view.line67.comment version will spew output to win32traceutil.
debug = 0
if debug:
    import win32traceutil

# 051847.python.shell_view.line72.comment markh is toying with an implementation that allows auto reload of a module
# 051848.python.shell_view.line73.comment if this attribute exists.
com_auto_reload = True


# 051849.python.shell_view.line77.comment Helper function to get a system IShellFolder interface, and the PIDL within
# 051850.python.shell_view.line78.comment that folder for an existing file/directory.
def GetFolderAndPIDLForPath(filename):
    desktop = shell.SHGetDesktopFolder()
    info = desktop.ParseDisplayName(0, None, os.path.abspath(filename))
    cchEaten, pidl, attr = info
    # 051851.python.shell_view.line83.comment We must walk the ID list, looking for one child at a time.
    folder = desktop
    while len(pidl) > 1:
        this = pidl.pop(0)
        folder = folder.BindToObject([this], None, shell.IID_IShellFolder)
    # 051852.python.shell_view.line88.comment We are left with the pidl for the specific item.  Leave it as
    # 051853.python.shell_view.line89.comment a list, so it remains a valid PIDL.
    return folder, pidl


# 051854.python.shell_view.line93.comment A cache of pyclbr module objects, so we only parse a given filename once.
clbr_modules = {}  # Indexed by path, item is dict as returned from pyclbr


def get_clbr_for_file(path):
    try:
        objects = clbr_modules[path]
    except KeyError:
        dir, filename = os.path.split(path)
        base, ext = os.path.splitext(filename)
        objects = pyclbr.readmodule_ex(base, [dir])
        clbr_modules[path] = objects
    return objects


# 051856.python.shell_view.line108.comment Our COM interfaces.


# 051857.python.shell_view.line111.comment Base class for a shell folder.
# 051858.python.shell_view.line112.comment All child classes use a simple PIDL of the form:
# 051859.python.shell_view.line113.comment "object_type\0object_name[\0extra ...]"
class ShellFolderBase:
    _com_interfaces_ = [
        shell.IID_IBrowserFrameOptions,
        pythoncom.IID_IPersist,
        shell.IID_IPersistFolder,
        shell.IID_IShellFolder,
    ]

    _public_methods_ = (
        shellcon.IBrowserFrame_Methods
        + shellcon.IPersistFolder_Methods
        + shellcon.IShellFolder_Methods
    )

    def GetFrameOptions(self, mask):
        # 051860.python.shell_view.line129.comment print("GetFrameOptions", self, mask)
        return 0

    def ParseDisplayName(self, hwnd, reserved, displayName, attr):
        print("ParseDisplayName", displayName)
        # 051861.python.shell_view.line134.comment return cchEaten, pidl, attr

    def BindToStorage(self, pidl, bc, iid):
        print("BTS", iid, IIDToInterfaceName(iid))

    def BindToObject(self, pidl, bc, iid):
        # 051862.python.shell_view.line140.comment We may be passed a set of relative PIDLs here - ie
        # 051863.python.shell_view.line141.comment [pidl_of_dir, pidl_of_child_dir, pidl_of_file, pidl_of_function]
        # 051864.python.shell_view.line142.comment But each of our PIDLs keeps the fully qualified name anyway - so
        # 051865.python.shell_view.line143.comment just jump directly to the last.
        final_pidl = pidl[-1]
        typ, extra = final_pidl.split("\0", 1)
        if typ == "directory":
            klass = ShellFolderDirectory
        elif typ == "file":
            klass = ShellFolderFile
        elif typ == "object":
            klass = ShellFolderObject
        else:
            raise RuntimeError(f"What is {typ!r}")
        ret = wrap(klass(extra), iid, useDispatcher=(debug > 0))
        return ret


# 051866.python.shell_view.line158.comment A ShellFolder for an object with CHILDREN on the file system
# 051867.python.shell_view.line159.comment Note that this means our "File" folder is *not* a 'FileSystem' folder,
# 051868.python.shell_view.line160.comment as it's children (functions and classes) are not on the file system.
# 051869.python.shell_view.line161.comment
class ShellFolderFileSystem(ShellFolderBase):
    def _GetFolderAndPIDLForPIDL(self, my_idl):
        typ, name = my_idl[0].split("\0")
        return GetFolderAndPIDLForPath(name)

    # 051870.python.shell_view.line167.comment Interface methods
    def CompareIDs(self, param, id1, id2):
        if id1 < id2:
            return -1
        if id1 == id2:
            return 0
        return 1

    def GetUIObjectOf(self, hwndOwner, pidls, iid, inout):
        # 051871.python.shell_view.line176.comment delegate to the shell.
        assert len(pidls) == 1, "oops - aren't expecting more than one!"
        pidl = pidls[0]
        folder, child_pidl = self._GetFolderAndPIDLForPIDL(pidl)
        try:
            inout, ret = folder.GetUIObjectOf(hwndOwner, [child_pidl], iid, inout, iid)
        except pythoncom.com_error as exc:
            raise COMException(hresult=exc.hresult)
        return inout, ret
        # 051872.python.shell_view.line185.comment return object of IID

    def GetDisplayNameOf(self, pidl, flags):
        # 051873.python.shell_view.line188.comment delegate to the shell.
        folder, child_pidl = self._GetFolderAndPIDLForPIDL(pidl)
        ret = folder.GetDisplayNameOf(child_pidl, flags)
        return ret

    def GetAttributesOf(self, pidls, attrFlags):
        ret_flags = -1
        for pidl in pidls:
            pidl = pidl[0]  # ??
            typ, name = pidl.split("\0")
            flags = shellcon.SHGFI_ATTRIBUTES
            rc, info = shell.SHGetFileInfo(name, 0, flags)
            hIcon, iIcon, dwAttr, name, typeName = info
            # 051875.python.shell_view.line201.comment All our items, even files, have sub-items
            extras = (
                shellcon.SFGAO_HASSUBFOLDER
                | shellcon.SFGAO_FOLDER
                | shellcon.SFGAO_FILESYSANCESTOR
                | shellcon.SFGAO_BROWSABLE
            )
            ret_flags &= dwAttr | extras
        return ret_flags


class ShellFolderDirectory(ShellFolderFileSystem):
    def __init__(self, path):
        self.path = os.path.abspath(path)

    def CreateViewObject(self, hwnd, iid):
        # 051876.python.shell_view.line217.comment delegate to the shell.
        folder, child_pidl = GetFolderAndPIDLForPath(self.path)
        return folder.CreateViewObject(hwnd, iid)

    def EnumObjects(self, hwndOwner, flags):
        pidls = []
        for fname in os.listdir(self.path):
            fqn = os.path.join(self.path, fname)
            if os.path.isdir(fqn):
                type_name = "directory"
                type_class = ShellFolderDirectory
            else:
                base, ext = os.path.splitext(fname)
                if ext in [".py", ".pyw"]:
                    type_class = ShellFolderFile
                    type_name = "file"
                else:
                    type_class = None
            if type_class is not None:
                pidls.append([type_name + "\0" + fqn])
        return NewEnum(pidls, iid=shell.IID_IEnumIDList, useDispatcher=(debug > 0))

    def GetDisplayNameOf(self, pidl, flags):
        final_pidl = pidl[-1]
        full_fname = final_pidl.split("\0")[-1]
        return os.path.split(full_fname)[-1]

    def GetAttributesOf(self, pidls, attrFlags):
        return (
            shellcon.SFGAO_HASSUBFOLDER
            | shellcon.SFGAO_FOLDER
            | shellcon.SFGAO_FILESYSANCESTOR
            | shellcon.SFGAO_BROWSABLE
        )


# 051877.python.shell_view.line253.comment As per comments above, even though this manages a file, it is *not* a
# 051878.python.shell_view.line254.comment ShellFolderFileSystem, as the children are not on the file system.
class ShellFolderFile(ShellFolderBase):
    def __init__(self, path):
        self.path = os.path.abspath(path)

    def EnumObjects(self, hwndOwner, flags):
        objects = get_clbr_for_file(self.path)
        pidls = []
        for name in objects:
            pidls.append(["object\0" + self.path + "\0" + name])
        return NewEnum(pidls, iid=shell.IID_IEnumIDList, useDispatcher=(debug > 0))

    def GetAttributesOf(self, pidls, attrFlags):
        ret_flags = -1
        for pidl in pidls:
            assert len(pidl) == 1, "Expecting relative pidls"
            pidl = pidl[0]
            typ, filename, obname = pidl.split("\0")
            obs = get_clbr_for_file(filename)
            ob = obs[obname]
            flags = (
                shellcon.SFGAO_BROWSABLE
                | shellcon.SFGAO_FOLDER
                | shellcon.SFGAO_FILESYSANCESTOR
            )
            if hasattr(ob, "methods"):
                flags |= shellcon.SFGAO_HASSUBFOLDER
            ret_flags &= flags
        return ret_flags

    def GetDisplayNameOf(self, pidl, flags):
        assert len(pidl) == 1, "Expecting relative PIDL"
        typ, fname, obname = pidl[0].split("\0")
        fqname = os.path.splitext(fname)[0] + "." + obname
        if flags & shellcon.SHGDN_INFOLDER:
            ret = obname
        else:  # SHGDN_NORMAL is the default
            ret = fqname
        # 051880.python.shell_view.line292.comment No need to look at the SHGDN_FOR* modifiers.
        return ret

    def CreateViewObject(self, hwnd, iid):
        return wrap(ScintillaShellView(hwnd, self.path), iid, useDispatcher=debug > 0)


# 051881.python.shell_view.line299.comment A ShellFolder for our Python objects
class ShellFolderObject(ShellFolderBase):
    def __init__(self, details):
        self.path, details = details.split("\0")
        if details.find(".") > 0:
            self.class_name, self.method_name = details.split(".")
        else:
            self.class_name = details
            self.method_name = None

    def CreateViewObject(self, hwnd, iid):
        mod_objects = get_clbr_for_file(self.path)
        object = mod_objects[self.class_name]
        if self.method_name is None:
            lineno = object.lineno
        else:
            lineno = object.methods[self.method_name]
            return wrap(
                ScintillaShellView(hwnd, self.path, lineno),
                iid,
                useDispatcher=debug > 0,
            )

    def EnumObjects(self, hwndOwner, flags):
        assert self.method_name is None, "Should not be enuming methods!"
        mod_objects = get_clbr_for_file(self.path)
        my_objects = mod_objects[self.class_name]
        pidls = []
        for func_name in my_objects.methods:
            pidl = ["object\0" + self.path + "\0" + self.class_name + "." + func_name]
            pidls.append(pidl)
        return NewEnum(pidls, iid=shell.IID_IEnumIDList, useDispatcher=(debug > 0))

    def GetDisplayNameOf(self, pidl, flags):
        assert len(pidl) == 1, "Expecting relative PIDL"
        typ, fname, obname = pidl[0].split("\0")
        class_name, method_name = obname.split(".")
        fqname = os.path.splitext(fname)[0] + "." + obname
        if flags & shellcon.SHGDN_INFOLDER:
            ret = method_name
        else:  # SHGDN_NORMAL is the default
            ret = fqname
        # 051883.python.shell_view.line341.comment No need to look at the SHGDN_FOR* modifiers.
        return ret

    def GetAttributesOf(self, pidls, attrFlags):
        ret_flags = -1
        for pidl in pidls:
            assert len(pidl) == 1, "Expecting relative pidls"
            flags = (
                shellcon.SFGAO_BROWSABLE
                | shellcon.SFGAO_FOLDER
                | shellcon.SFGAO_FILESYSANCESTOR
            )
            ret_flags &= flags
        return ret_flags


# 051884.python.shell_view.line357.comment The "Root" folder of our namespace.  As all children are directories,
# 051885.python.shell_view.line358.comment it is derived from ShellFolderFileSystem
# 051886.python.shell_view.line359.comment This is the only COM object actually registered and externally created.
class ShellFolderRoot(ShellFolderFileSystem):
    _reg_progid_ = "Python.ShellExtension.Folder"
    _reg_desc_ = "Python Path Shell Browser"
    _reg_clsid_ = "{f6287035-3074-4cb5-a8a6-d3c80e206944}"

    def GetClassID(self):
        return self._reg_clsid_

    def Initialize(self, pidl):
        # 051887.python.shell_view.line369.comment This is the PIDL of us, as created by the shell.  This is our
        # 051888.python.shell_view.line370.comment top-level ID.  All other items under us have PIDLs defined
        # 051889.python.shell_view.line371.comment by us - see the notes at the top of the file.
        # 051890.python.shell_view.line372.comment print("Initialize called with pidl={pidl!r}")
        self.pidl = pidl

    def CreateViewObject(self, hwnd, iid):
        return wrap(FileSystemView(self, hwnd), iid, useDispatcher=debug > 0)

    def EnumObjects(self, hwndOwner, flags):
        items = [["directory\0" + p] for p in sys.path if os.path.isdir(p)]
        return NewEnum(items, iid=shell.IID_IEnumIDList, useDispatcher=(debug > 0))

    def GetDisplayNameOf(self, pidl, flags):
        # 051891.python.shell_view.line383.comment # return full path for sys.path dirs, since they don't appear under a parent folder
        final_pidl = pidl[-1]
        display_name = final_pidl.split("\0")[-1]
        return display_name


# 051892.python.shell_view.line389.comment Simple shell view implementations


# 051893.python.shell_view.line392.comment Uses a builtin listview control to display simple lists of directories
# 051894.python.shell_view.line393.comment or filenames.
class FileSystemView:
    _public_methods_ = shellcon.IShellView_Methods
    _com_interfaces_ = [
        pythoncom.IID_IOleWindow,
        shell.IID_IShellView,
    ]

    def __init__(self, folder, hwnd):
        self.hwnd_parent = hwnd  # provided by explorer.
        self.hwnd = None  # intermediate window for catching command notifications.
        self.hwnd_child = None  # our ListView
        self.activate_state = None
        self.hmenu = None
        self.browser = None
        self.folder = folder
        self.children = None

    # 051898.python.shell_view.line411.comment IOleWindow
    def GetWindow(self):
        return self.hwnd

    def ContextSensitiveHelp(self, enter_mode):
        raise COMException(hresult=winerror.E_NOTIMPL)

    # 051899.python.shell_view.line418.comment IShellView
    def CreateViewWindow(self, prev, settings, browser, rect):
        print("FileSystemView.CreateViewWindow", prev, settings, browser, rect)
        self.cur_foldersettings = settings
        self.browser = browser
        self._CreateMainWindow(prev, settings, browser, rect)
        self._CreateChildWindow(prev)

        # 051900.python.shell_view.line426.comment This isn't part of the sample, but the most convenient place to
        # 051901.python.shell_view.line427.comment test/demonstrate how you can get an IShellBrowser from a HWND
        # 051902.python.shell_view.line428.comment (but ONLY when you are in the same process as the IShellBrowser!)
        # 051903.python.shell_view.line429.comment Obviously it is not necessary here - we already have the browser!
        browser_ad = win32gui.SendMessage(self.hwnd_parent, win32con.WM_USER + 7, 0, 0)
        browser_ob = pythoncom.ObjectFromAddress(browser_ad, shell.IID_IShellBrowser)
        assert browser == browser_ob
        # 051904.python.shell_view.line433.comment and make a call on the object to prove it doesn't die :)
        assert browser.QueryActiveShellView() == browser_ob.QueryActiveShellView()

    def _CreateMainWindow(self, prev, settings, browser, rect):
        # 051905.python.shell_view.line437.comment Creates a parent window that hosts the view window.  This window
        # 051906.python.shell_view.line438.comment gets the control notifications etc sent from the child.
        style = win32con.WS_CHILD | win32con.WS_VISIBLE  #
        wclass_name = "ShellViewDemo_DefView"
        # 051908.python.shell_view.line441.comment Register the Window class.
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32gui.dllhandle
        wc.lpszClassName = wclass_name
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        try:
            win32gui.RegisterClass(wc)
        except win32gui.error as details:
            # 051909.python.shell_view.line449.comment Should only happen when this module is reloaded
            if details[0] != winerror.ERROR_CLASS_ALREADY_EXISTS:
                raise

        message_map = {
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_COMMAND: self.OnCommand,
            win32con.WM_NOTIFY: self.OnNotify,
            win32con.WM_CONTEXTMENU: self.OnContextMenu,
            win32con.WM_SIZE: self.OnSize,
        }

        self.hwnd = win32gui.CreateWindow(
            wclass_name,
            "",
            style,
            rect[0],
            rect[1],
            rect[2] - rect[0],
            rect[3] - rect[1],
            self.hwnd_parent,
            0,
            win32gui.dllhandle,
            None,
        )
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_WNDPROC, message_map)
        print("View 's hwnd is", self.hwnd)
        return self.hwnd

    def _CreateChildWindow(self, prev):
        # 051910.python.shell_view.line479.comment Creates the list view window.
        assert self.hwnd_child is None, "already have a window"
        assert self.cur_foldersettings is not None, "no settings"
        style = (
            win32con.WS_CHILD
            | win32con.WS_VISIBLE
            | win32con.WS_BORDER
            | commctrl.LVS_SHAREIMAGELISTS
            | commctrl.LVS_EDITLABELS
        )

        view_mode, view_flags = self.cur_foldersettings
        if view_mode == shellcon.FVM_ICON:
            style |= commctrl.LVS_ICON | commctrl.LVS_AUTOARRANGE
        elif view_mode == shellcon.FVM_SMALLICON:
            style |= commctrl.LVS_SMALLICON | commctrl.LVS_AUTOARRANGE
        elif view_mode == shellcon.FVM_LIST:
            style |= commctrl.LVS_LIST | commctrl.LVS_AUTOARRANGE
        elif view_mode == shellcon.FVM_DETAILS:
            style |= commctrl.LVS_REPORT | commctrl.LVS_AUTOARRANGE
        else:
            # 051911.python.shell_view.line500.comment XP 'thumbnails' etc
            view_mode = shellcon.FVM_DETAILS
            # 051912.python.shell_view.line502.comment Default to 'report'
            style |= commctrl.LVS_REPORT | commctrl.LVS_AUTOARRANGE

        for f_flag, l_flag in [
            (shellcon.FWF_SINGLESEL, commctrl.LVS_SINGLESEL),
            (shellcon.FWF_ALIGNLEFT, commctrl.LVS_ALIGNLEFT),
            (shellcon.FWF_SHOWSELALWAYS, commctrl.LVS_SHOWSELALWAYS),
        ]:
            if view_flags & f_flag:
                style |= l_flag

        self.hwnd_child = win32gui.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            "SysListView32",
            None,
            style,
            0,
            0,
            0,
            0,
            self.hwnd,
            1000,
            0,
            None,
        )

        cr = win32gui.GetClientRect(self.hwnd)
        win32gui.MoveWindow(self.hwnd_child, 0, 0, cr[2] - cr[0], cr[3] - cr[1], True)

        # 051913.python.shell_view.line531.comment Setup the columns for the view.
        lvc, extras = win32gui_struct.PackLVCOLUMN(
            fmt=commctrl.LVCFMT_LEFT, subItem=1, text="Name", cx=300
        )
        win32gui.SendMessage(self.hwnd_child, commctrl.LVM_INSERTCOLUMN, 0, lvc)

        lvc, extras = win32gui_struct.PackLVCOLUMN(
            fmt=commctrl.LVCFMT_RIGHT, subItem=1, text="Exists", cx=50
        )
        win32gui.SendMessage(self.hwnd_child, commctrl.LVM_INSERTCOLUMN, 1, lvc)
        # 051914.python.shell_view.line541.comment and fill it with the content
        self.Refresh()

    def GetCurrentInfo(self):
        return self.cur_foldersettings

    def UIActivate(self, activate_state):
        print("OnActivate")

    def _OnActivate(self, activate_state):
        if self.activate_state == activate_state:
            return
        self._OnDeactivate()  # restore menu's first, if necessary.
        if activate_state != shellcon.SVUIA_DEACTIVATE:
            assert self.hmenu is None, "Should have destroyed it!"
            self.hmenu = win32gui.CreateMenu()
            widths = 0, 0, 0, 0, 0, 0
            # 051916.python.shell_view.line558.comment Ask explorer to add its standard items.
            self.browser.InsertMenusSB(self.hmenu, widths)
            # 051917.python.shell_view.line560.comment Merge with these standard items
            self._MergeMenus(activate_state)
            self.browser.SetMenuSB(self.hmenu, 0, self.hwnd)
        self.activate_state = activate_state

    def _OnDeactivate(self):
        if self.browser is not None and self.hmenu is not None:
            self.browser.SetMenuSB(0, 0, 0)
            self.browser.RemoveMenusSB(self.hmenu)
            win32gui.DestroyMenu(self.hmenu)
            self.hmenu = None
        self.hsubmenus = None
        self.activate_state = shellcon.SVUIA_DEACTIVATE

    def _MergeMenus(self, activate_state):
        # 051918.python.shell_view.line575.comment Merge the operations we support into the top-level menus.
        # 051919.python.shell_view.line576.comment NOTE: This function it *not* called each time the selection changes.
        # 051920.python.shell_view.line577.comment SVUIA_ACTIVATE_FOCUS really means "have a selection?"
        have_sel = activate_state == shellcon.SVUIA_ACTIVATE_FOCUS
        # 051921.python.shell_view.line579.comment only do "file" menu here, and only 1 item on it!
        mid = shellcon.FCIDM_MENU_FILE
        # 051922.python.shell_view.line581.comment Get the hmenu for the menu
        buf, extras = win32gui_struct.EmptyMENUITEMINFO(win32con.MIIM_SUBMENU)
        win32gui.GetMenuItemInfo(self.hmenu, mid, False, buf)
        data = win32gui_struct.UnpackMENUITEMINFO(buf)
        submenu = data[3]
        print("Do someting with the file menu!")

    def Refresh(self):
        stateMask = commctrl.LVIS_SELECTED | commctrl.LVIS_DROPHILITED
        state = 0
        self.children = []
        # 051923.python.shell_view.line592.comment Enumerate and store the child PIDLs
        for cid in self.folder.EnumObjects(self.hwnd, 0):
            self.children.append(cid)

        for row_index, data in enumerate(self.children):
            assert len(data) == 1, "expecting just a child PIDL"
            typ, path = data[0].split("\0")
            desc = os.path.exists(path) and "Yes" or "No"
            prop_vals = (path, desc)
            # 051924.python.shell_view.line601.comment first col
            data, extras = win32gui_struct.PackLVITEM(
                item=row_index,
                subItem=0,
                text=prop_vals[0],
                state=state,
                stateMask=stateMask,
            )
            win32gui.SendMessage(
                self.hwnd_child, commctrl.LVM_INSERTITEM, row_index, data
            )
            # 051925.python.shell_view.line612.comment rest of the cols.
            col_index = 1
            for prop_val in prop_vals[1:]:
                data, extras = win32gui_struct.PackLVITEM(
                    item=row_index, subItem=col_index, text=prop_val
                )

                win32gui.SendMessage(self.hwnd_child, commctrl.LVM_SETITEM, 0, data)
                col_index += 1

    def SelectItem(self, pidl, flag):
        # 051926.python.shell_view.line623.comment For the sake of brevity, we don't implement this yet.
        # 051927.python.shell_view.line624.comment You would need to locate the index of the item in the shell-view
        # 051928.python.shell_view.line625.comment with that PIDL, then ask the list-view to select it.
        print("Please implement SelectItem for PIDL", pidl)

    def GetItemObject(self, item_num, iid):
        raise COMException(hresult=winerror.E_NOTIMPL)

    def TranslateAccelerator(self, msg):
        return winerror.S_FALSE

    def DestroyViewWindow(self):
        win32gui.DestroyWindow(self.hwnd)
        self.hwnd = None
        print("Destroyed view window")

    # 051929.python.shell_view.line639.comment Message handlers.
    def OnDestroy(self, hwnd, msg, wparam, lparam):
        print("OnDestory")

    def OnCommand(self, hwnd, msg, wparam, lparam):
        print("OnCommand")

    def OnNotify(self, hwnd, msg, wparam, lparam):
        hwndFrom, idFrom, code = win32gui_struct.UnpackWMNOTIFY(lparam)
        # 051930.python.shell_view.line648.comment print("OnNotify code=0x%x (0x%x, 0x%x)" % (code, wparam, lparam))
        if code == commctrl.NM_SETFOCUS:
            # 051931.python.shell_view.line650.comment Control got focus - Explorer may not know - tell it
            if self.browser is not None:
                self.browser.OnViewWindowActive(None)
            # 051932.python.shell_view.line653.comment And do our menu thang
            self._OnActivate(shellcon.SVUIA_ACTIVATE_FOCUS)
        elif code == commctrl.NM_KILLFOCUS:
            self._OnDeactivate()
        elif code == commctrl.NM_DBLCLK:
            # 051933.python.shell_view.line658.comment This DblClick implementation leaves a little to be desired :)
            # 051934.python.shell_view.line659.comment It demonstrates some useful concepts, such as asking the
            # 051935.python.shell_view.line660.comment folder for its context-menu and invoking a command from it.
            # 051936.python.shell_view.line661.comment However, as our folder delegates IContextMenu to the shell
            # 051937.python.shell_view.line662.comment itself, the end result is that the folder is opened in
            # 051938.python.shell_view.line663.comment its "normal" place in Windows explorer rather than inside
            # 051939.python.shell_view.line664.comment our shell-extension.
            # 051940.python.shell_view.line665.comment Determine the selected items.
            sel = []
            n = -1
            while 1:
                n = win32gui.SendMessage(
                    self.hwnd_child, commctrl.LVM_GETNEXTITEM, n, commctrl.LVNI_SELECTED
                )
                if n == -1:
                    break
                sel.append(self.children[n][-1:])
            print("Selection is", sel)
            hmenu = win32gui.CreateMenu()
            try:
                # 051941.python.shell_view.line678.comment Get the IContextMenu for the items.
                inout, cm = self.folder.GetUIObjectOf(
                    self.hwnd_parent, sel, shell.IID_IContextMenu, 0
                )

                # 051942.python.shell_view.line683.comment As per 'Q179911', we need to determine if the default operation
                # 051943.python.shell_view.line684.comment should be 'open' or 'explore'
                flags = shellcon.CMF_DEFAULTONLY
                try:
                    self.browser.GetControlWindow(shellcon.FCW_TREE)
                    flags |= shellcon.CMF_EXPLORE
                except pythoncom.com_error:
                    pass
                # 051944.python.shell_view.line691.comment *sob* - delegating to the shell does work - but lands us
                # 051945.python.shell_view.line692.comment in the original location.  Q179911 also shows that
                # 051946.python.shell_view.line693.comment ShellExecuteEx should work - but I can't make it work as
                # 051947.python.shell_view.line694.comment described (XP: function call succeeds, but another thread
                # 051948.python.shell_view.line695.comment shows a dialog with text of E_INVALID_PARAM, and new
                # 051949.python.shell_view.line696.comment Explorer window opens with desktop view. Vista: function
                # 051950.python.shell_view.line697.comment call succeeds, but no window created at all.
                # 051951.python.shell_view.line698.comment On Vista, I'd love to get an IExplorerBrowser interface
                # 051952.python.shell_view.line699.comment from the shell, but a QI fails, and although the
                # 051953.python.shell_view.line700.comment IShellBrowser does appear to support IServiceProvider, I
                # 051954.python.shell_view.line701.comment still can't get it
                if 0:
                    id_cmd_first = 1  # TrackPopupMenu makes it hard to use 0
                    cm.QueryContextMenu(hmenu, 0, id_cmd_first, -1, flags)
                    # 051956.python.shell_view.line705.comment Find the default item in the returned menu.
                    cmd = win32gui.GetMenuDefaultItem(hmenu, False, 0)
                    if cmd == -1:
                        print("Oops: _doDefaultActionFor found no default menu")
                    else:
                        ci = (
                            0,
                            self.hwnd_parent,
                            cmd - id_cmd_first,
                            None,
                            None,
                            0,
                            0,
                            0,
                        )
                        cm.InvokeCommand(ci)
                else:
                    rv = shell.ShellExecuteEx(
                        hwnd=self.hwnd_parent,
                        nShow=win32con.SW_NORMAL,
                        lpClass="folder",
                        lpVerb="explore",
                        lpIDList=sel[0],
                    )
                    print("ShellExecuteEx returned", rv)
            finally:
                win32gui.DestroyMenu(hmenu)

    def OnContextMenu(self, hwnd, msg, wparam, lparam):
        # 051957.python.shell_view.line734.comment Get the selected items.
        pidls = []
        n = -1
        while 1:
            n = win32gui.SendMessage(
                self.hwnd_child, commctrl.LVM_GETNEXTITEM, n, commctrl.LVNI_SELECTED
            )
            if n == -1:
                break
            pidls.append(self.children[n][-1:])

        spt = win32api.GetCursorPos()
        if not pidls:
            print("Ignoring background click")
            return
        # 051958.python.shell_view.line749.comment Get the IContextMenu for the items.
        inout, cm = self.folder.GetUIObjectOf(
            self.hwnd_parent, pidls, shell.IID_IContextMenu, 0
        )
        hmenu = win32gui.CreatePopupMenu()
        sel = None
        # 051959.python.shell_view.line755.comment As per 'Q179911', we need to determine if the default operation
        # 051960.python.shell_view.line756.comment should be 'open' or 'explore'
        try:
            flags = 0
            try:
                self.browser.GetControlWindow(shellcon.FCW_TREE)
                flags |= shellcon.CMF_EXPLORE
            except pythoncom.com_error:
                pass
            id_cmd_first = 1  # TrackPopupMenu makes it hard to use 0
            cm.QueryContextMenu(hmenu, 0, id_cmd_first, -1, flags)
            tpm_flags = (
                win32con.TPM_LEFTALIGN
                | win32con.TPM_RETURNCMD
                | win32con.TPM_RIGHTBUTTON
            )
            sel = win32gui.TrackPopupMenu(
                hmenu, tpm_flags, spt[0], spt[1], 0, self.hwnd, None
            )
            print("TrackPopupMenu returned", sel)
        finally:
            win32gui.DestroyMenu(hmenu)
        if sel:
            ci = 0, self.hwnd_parent, sel - id_cmd_first, None, None, 0, 0, 0
            cm.InvokeCommand(ci)

    def OnSize(self, hwnd, msg, wparam, lparam):
        # 051962.python.shell_view.line782.comment print("OnSize", self.hwnd_child, win32api.LOWORD(lparam), win32api.HIWORD(lparam))
        if self.hwnd_child is not None:
            x = win32api.LOWORD(lparam)
            y = win32api.HIWORD(lparam)
            win32gui.MoveWindow(self.hwnd_child, 0, 0, x, y, False)


# 051963.python.shell_view.line789.comment This uses scintilla to display a filename, and optionally jump to a line
# 051964.python.shell_view.line790.comment number.
class ScintillaShellView:
    _public_methods_ = shellcon.IShellView_Methods
    _com_interfaces_ = [
        pythoncom.IID_IOleWindow,
        shell.IID_IShellView,
    ]

    def __init__(self, hwnd, filename, lineno=None):
        self.filename = filename
        self.lineno = lineno
        self.hwnd_parent = hwnd
        self.hwnd = None

    def _SendSci(self, msg, wparam=0, lparam=0):
        return win32gui.SendMessage(self.hwnd, msg, wparam, lparam)

    # 051965.python.shell_view.line807.comment IShellView
    def CreateViewWindow(self, prev, settings, browser, rect):
        print("ScintillaShellView.CreateViewWindow", prev, settings, browser, rect)
        # 051966.python.shell_view.line810.comment Make sure scintilla.dll is loaded.  If not, find it on sys.path
        # 051967.python.shell_view.line811.comment (which it generally is for Pythonwin)
        try:
            win32api.GetModuleHandle("Scintilla.dll")
        except win32api.error:
            for p in sys.path:
                fname = os.path.join(p, "Scintilla.dll")
                if not os.path.isfile(fname):
                    fname = os.path.join(p, "Build", "Scintilla.dll")
                if os.path.isfile(fname):
                    win32api.LoadLibrary(fname)
                    break
            else:
                raise RuntimeError("Can't find scintilla!")

        style = (
            win32con.WS_CHILD
            | win32con.WS_VSCROLL
            | win32con.WS_HSCROLL
            | win32con.WS_CLIPCHILDREN
            | win32con.WS_VISIBLE
        )
        self.hwnd = win32gui.CreateWindow(
            "Scintilla",
            "Scintilla",
            style,
            rect[0],
            rect[1],
            rect[2] - rect[0],
            rect[3] - rect[1],
            self.hwnd_parent,
            1000,
            0,
            None,
        )

        message_map = {
            win32con.WM_SIZE: self.OnSize,
        }
        # 051968.python.shell_view.line849.comment win32gui.SetWindowLong(self.hwnd, win32con.GWL_WNDPROC, message_map)

        file_data = open(self.filename, "U").read()

        self._SetupLexer()
        self._SendSci(scintillacon.SCI_ADDTEXT, len(file_data), file_data)
        if self.lineno is not None:
            self._SendSci(scintillacon.SCI_GOTOLINE, self.lineno)
        print("Scintilla's hwnd is", self.hwnd)

    def _SetupLexer(self):
        h = self.hwnd
        styles = [
            ((0, 0, 200, 0, 0x808080), None, scintillacon.SCE_P_DEFAULT),
            ((0, 2, 200, 0, 0x008000), None, scintillacon.SCE_P_COMMENTLINE),
            ((0, 2, 200, 0, 0x808080), None, scintillacon.SCE_P_COMMENTBLOCK),
            ((0, 0, 200, 0, 0x808000), None, scintillacon.SCE_P_NUMBER),
            ((0, 0, 200, 0, 0x008080), None, scintillacon.SCE_P_STRING),
            ((0, 0, 200, 0, 0x008080), None, scintillacon.SCE_P_CHARACTER),
            ((0, 0, 200, 0, 0x008080), None, scintillacon.SCE_P_TRIPLE),
            ((0, 0, 200, 0, 0x008080), None, scintillacon.SCE_P_TRIPLEDOUBLE),
            ((0, 0, 200, 0, 0x000000), 0x008080, scintillacon.SCE_P_STRINGEOL),
            ((0, 1, 200, 0, 0x800000), None, scintillacon.SCE_P_WORD),
            ((0, 1, 200, 0, 0xFF0000), None, scintillacon.SCE_P_CLASSNAME),
            ((0, 1, 200, 0, 0x808000), None, scintillacon.SCE_P_DEFNAME),
            ((0, 0, 200, 0, 0x000000), None, scintillacon.SCE_P_OPERATOR),
            ((0, 0, 200, 0, 0x000000), None, scintillacon.SCE_P_IDENTIFIER),
        ]
        self._SendSci(scintillacon.SCI_SETLEXER, scintillacon.SCLEX_PYTHON, 0)
        self._SendSci(scintillacon.SCI_SETSTYLEBITS, 5)
        baseFormat = (-402653169, 0, 200, 0, 0, 0, 49, "Courier New")
        for f, bg, stylenum in styles:
            self._SendSci(scintillacon.SCI_STYLESETFORE, stylenum, f[4])
            self._SendSci(scintillacon.SCI_STYLESETFONT, stylenum, baseFormat[7])
            if f[1] & 1:
                self._SendSci(scintillacon.SCI_STYLESETBOLD, stylenum, 1)
            else:
                self._SendSci(scintillacon.SCI_STYLESETBOLD, stylenum, 0)
            if f[1] & 2:
                self._SendSci(scintillacon.SCI_STYLESETITALIC, stylenum, 1)
            else:
                self._SendSci(scintillacon.SCI_STYLESETITALIC, stylenum, 0)
            self._SendSci(
                scintillacon.SCI_STYLESETSIZE, stylenum, int(baseFormat[2] / 20)
            )
            if bg is not None:
                self._SendSci(scintillacon.SCI_STYLESETBACK, stylenum, bg)
            self._SendSci(
                scintillacon.SCI_STYLESETEOLFILLED, stylenum, 1
            )  # Only needed for unclosed strings.

    # 051970.python.shell_view.line900.comment IOleWindow
    def GetWindow(self):
        return self.hwnd

    def UIActivate(self, activate_state):
        print("OnActivate")

    def DestroyViewWindow(self):
        win32gui.DestroyWindow(self.hwnd)
        self.hwnd = None
        print("Destroyed scintilla window")

    def TranslateAccelerator(self, msg):
        return winerror.S_FALSE

    def OnSize(self, hwnd, msg, wparam, lparam):
        x = win32api.LOWORD(lparam)
        y = win32api.HIWORD(lparam)
        win32gui.MoveWindow(self.hwnd, 0, 0, x, y, False)


def DllRegisterServer():
    import winreg

    key = winreg.CreateKey(
        winreg.HKEY_LOCAL_MACHINE,
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\"
        "Explorer\\Desktop\\Namespace\\" + ShellFolderRoot._reg_clsid_,
    )
    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, ShellFolderRoot._reg_desc_)
    # 051971.python.shell_view.line930.comment And special shell keys under our CLSID
    key = winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        "CLSID\\" + ShellFolderRoot._reg_clsid_ + "\\ShellFolder",
    )
    # 051972.python.shell_view.line935.comment 'Attributes' is an int stored as a binary! use struct
    attr = (
        shellcon.SFGAO_FOLDER | shellcon.SFGAO_HASSUBFOLDER | shellcon.SFGAO_BROWSABLE
    )
    import struct

    s = struct.pack("i", attr)
    winreg.SetValueEx(key, "Attributes", 0, winreg.REG_BINARY, s)
    print(ShellFolderRoot._reg_desc_, "registration complete.")


def DllUnregisterServer():
    import winreg

    try:
        key = winreg.DeleteKey(
            winreg.HKEY_LOCAL_MACHINE,
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\"
            "Explorer\\Desktop\\Namespace\\" + ShellFolderRoot._reg_clsid_,
        )
    except OSError as details:
        import errno

        if details.errno != errno.ENOENT:
            raise
    print(ShellFolderRoot._reg_desc_, "unregistration complete.")


if __name__ == "__main__":
    from win32com.server import register

    register.UseCommandLine(
        ShellFolderRoot,
        debug=debug,
        finalize_register=DllRegisterServer,
        finalize_unregister=DllUnregisterServer,
    )
