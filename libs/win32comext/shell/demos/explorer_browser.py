# 051544.python.explorer_browser.line1.comment A sample of using Vista's IExplorerBrowser interfaces...
# 051545.python.explorer_browser.line2.comment Currently doesn't quite work:
# 051546.python.explorer_browser.line3.comment * CPU sits at 100% while running.

import sys

import pythoncom
import win32api
import win32con
import win32gui
from win32com.server.util import unwrap, wrap
from win32com.shell import shell, shellcon

# 051547.python.explorer_browser.line14.comment event handler for the browser.
IExplorerBrowserEvents_Methods = """OnNavigationComplete OnNavigationFailed
                                    OnNavigationPending OnViewCreated""".split()


class EventHandler:
    _com_interfaces_ = [shell.IID_IExplorerBrowserEvents]
    _public_methods_ = IExplorerBrowserEvents_Methods

    def OnNavigationComplete(self, pidl):
        print("OnNavComplete", pidl)

    def OnNavigationFailed(self, pidl):
        print("OnNavigationFailed", pidl)

    def OnNavigationPending(self, pidl):
        print("OnNavigationPending", pidl)

    def OnViewCreated(self, view):
        print("OnViewCreated", view)
        # 051548.python.explorer_browser.line34.comment And if our demo view has been registered, it may well
        # 051549.python.explorer_browser.line35.comment be that view!
        try:
            pyview = unwrap(view)
            print("and look - it's a Python implemented view!", pyview)
        except ValueError:
            pass


class MainWindow:
    def __init__(self):
        message_map = {
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_COMMAND: self.OnCommand,
            win32con.WM_SIZE: self.OnSize,
        }
        # 051550.python.explorer_browser.line50.comment Register the Window class.
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "test_explorer_browser"
        wc.lpfnWndProc = message_map  # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(wc)
        # 051552.python.explorer_browser.line56.comment Create the Window.
        style = win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE
        self.hwnd = win32gui.CreateWindow(
            classAtom,
            "Python IExplorerBrowser demo",
            style,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            hinst,
            None,
        )
        eb = pythoncom.CoCreateInstance(
            shellcon.CLSID_ExplorerBrowser,
            None,
            pythoncom.CLSCTX_ALL,
            shell.IID_IExplorerBrowser,
        )
        # 051553.python.explorer_browser.line77.comment as per MSDN docs, hook up events early
        self.event_cookie = eb.Advise(wrap(EventHandler()))

        eb.SetOptions(shellcon.EBO_SHOWFRAMES)
        rect = win32gui.GetClientRect(self.hwnd)
        # 051554.python.explorer_browser.line82.comment Set the flags such that the folders autoarrange and non web view is presented
        flags = (shellcon.FVM_LIST, shellcon.FWF_AUTOARRANGE | shellcon.FWF_NOWEBVIEW)
        eb.Initialize(self.hwnd, rect, (0, shellcon.FVM_DETAILS))
        if len(sys.argv) == 2:
            # 051555.python.explorer_browser.line86.comment If an arg was specified, ask the desktop parse it.
            # 051556.python.explorer_browser.line87.comment You can pass anything explorer accepts as its '/e' argument -
            # 051557.python.explorer_browser.line88.comment eg, "::{guid}\::{guid}" etc.
            # 051558.python.explorer_browser.line89.comment "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}" is "My Computer"
            pidl = shell.SHGetDesktopFolder().ParseDisplayName(0, None, sys.argv[1])[1]
        else:
            # 051559.python.explorer_browser.line92.comment And start browsing at the root of the namespace.
            pidl = []
        eb.BrowseToIDList(pidl, shellcon.SBSP_ABSOLUTE)
        # 051560.python.explorer_browser.line95.comment and for some reason the "Folder" view in the navigator pane doesn't
        # 051561.python.explorer_browser.line96.comment magically synchronize itself - so let's do that ourself.
        # 051562.python.explorer_browser.line97.comment Get the tree control.
        sp = eb.QueryInterface(pythoncom.IID_IServiceProvider)
        try:
            tree = sp.QueryService(
                shell.IID_INameSpaceTreeControl, shell.IID_INameSpaceTreeControl
            )
        except pythoncom.com_error as exc:
            # 051563.python.explorer_browser.line104.comment this should really only fail if no "nav" frame exists...
            print(
                "Strange - failed to get the tree control even though "
                "we asked for a EBO_SHOWFRAMES"
            )
            print(exc)
        else:
            # 051564.python.explorer_browser.line111.comment get the IShellItem for the selection.
            si = shell.SHCreateItemFromIDList(pidl, shell.IID_IShellItem)
            # 051565.python.explorer_browser.line113.comment set it to selected.
            tree.SetItemState(si, shellcon.NSTCIS_SELECTED, shellcon.NSTCIS_SELECTED)

        # 051566.python.explorer_browser.line116.comment eb.FillFromObject(None, shellcon.EBF_NODROPTARGET);
        # 051567.python.explorer_browser.line117.comment eb.SetEmptyText("No known folders yet...");
        self.eb = eb

    def OnCommand(self, hwnd, msg, wparam, lparam):
        pass

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        print("tearing down ExplorerBrowser...")
        self.eb.Unadvise(self.event_cookie)
        self.eb.Destroy()
        self.eb = None
        print("shutting down app...")
        win32gui.PostQuitMessage(0)

    def OnSize(self, hwnd, msg, wparam, lparam):
        x = win32api.LOWORD(lparam)
        y = win32api.HIWORD(lparam)
        self.eb.SetRect(None, (0, 0, x, y))


def main():
    w = MainWindow()
    win32gui.PumpMessages()


if __name__ == "__main__":
    main()
