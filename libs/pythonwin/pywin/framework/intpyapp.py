# 037806.python.intpyapp.line1.comment intpyapp.py  - Interactive Python application class
# 037807.python.intpyapp.line2.comment
import os
import sys
import traceback

import __main__
import commctrl
import win32api
import win32con
import win32ui
from pywin.mfc import afxres, dialog, docview

from . import app, dbgcommands

lastLocateFileName = ".py"  # used in the "File/Locate" dialog...


# 037809.python.intpyapp.line19.comment todo - _SetupSharedMenu should be moved to a framework class.
def _SetupSharedMenu_(self):
    sharedMenu = self.GetSharedMenu()
    from pywin.framework import toolmenu

    toolmenu.SetToolsMenu(sharedMenu)
    from pywin.framework import help

    help.SetHelpMenuOtherHelp(sharedMenu)


docview.DocTemplate._SetupSharedMenu_ = _SetupSharedMenu_  # type: ignore[method-assign]


class MainFrame(app.MainFrame):
    def OnCreate(self, createStruct):
        self.closing = 0
        if app.MainFrame.OnCreate(self, createStruct) == -1:
            return -1
        style = (
            win32con.WS_CHILD
            | afxres.CBRS_SIZE_DYNAMIC
            | afxres.CBRS_TOP
            | afxres.CBRS_TOOLTIPS
            | afxres.CBRS_FLYBY
        )

        self.EnableDocking(afxres.CBRS_ALIGN_ANY)

        tb = win32ui.CreateToolBar(self, style | win32con.WS_VISIBLE)
        tb.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
        tb.LoadToolBar(win32ui.IDR_MAINFRAME)
        tb.EnableDocking(afxres.CBRS_ALIGN_ANY)
        tb.SetWindowText("Standard")
        self.DockControlBar(tb)
        # 037811.python.intpyapp.line54.comment Any other packages which use toolbars
        from pywin.debugger.debugger import PrepareControlBars

        PrepareControlBars(self)
        # 037812.python.intpyapp.line58.comment Note "interact" also uses dockable windows, but they already happen

        # 037813.python.intpyapp.line60.comment And a "Tools" menu on the main frame.
        menu = self.GetMenu()
        from . import toolmenu

        toolmenu.SetToolsMenu(menu, 2)
        # 037814.python.intpyapp.line65.comment And fix the "Help" menu on the main frame
        from pywin.framework import help

        help.SetHelpMenuOtherHelp(menu)

    def OnClose(self):
        try:
            import pywin.debugger

            if (
                pywin.debugger.currentDebugger is not None
                and pywin.debugger.currentDebugger.pumping
            ):
                try:
                    pywin.debugger.currentDebugger.close(1)
                except:
                    traceback.print_exc()
                return
        except win32ui.error:
            pass
        self.closing = 1
        self.SaveBarState("ToolbarDefault")
        self.SetActiveView(None)  # Otherwise MFC's OnClose may _not_ prompt for save.

        from pywin.framework import help

        help.FinalizeHelp()

        self.DestroyControlBar(afxres.AFX_IDW_TOOLBAR)
        self.DestroyControlBar(win32ui.ID_VIEW_TOOLBAR_DBG)

        return self._obj_.OnClose()

    def DestroyControlBar(self, id):
        try:
            bar = self.GetControlBar(id)
        except win32ui.error:
            return
        bar.DestroyWindow()

    def OnCommand(self, wparam, lparam):
        # 037816.python.intpyapp.line106.comment By default, the current MDI child frame will process WM_COMMAND
        # 037817.python.intpyapp.line107.comment messages before any docked control bars - even if the control bar
        # 037818.python.intpyapp.line108.comment has focus.  This is a problem for the interactive window when docked.
        # 037819.python.intpyapp.line109.comment Therefore, we detect the situation of a view having the main frame
        # 037820.python.intpyapp.line110.comment as its parent, and assume it must be a docked view (which it will in an MDI app)
        try:
            v = (
                self.GetActiveView()
            )  # Raise an exception if none - good - then we want default handling
            # 037822.python.intpyapp.line115.comment Main frame _does_ have a current view (ie, a docking view) - see if it wants it.
            if v.OnCommand(wparam, lparam):
                return 1
        except (win32ui.error, AttributeError):
            pass
        return self._obj_.OnCommand(wparam, lparam)


class InteractivePythonApp(app.CApp):
    # 037823.python.intpyapp.line124.comment This works if necessary - just we don't need to override the Run method.
    # 037824.python.intpyapp.line125.comment def Run(self):
    # 037825.python.intpyapp.line126.comment return self._obj_.Run()

    def HookCommands(self):
        app.CApp.HookCommands(self)
        dbgcommands.DebuggerCommandHandler().HookCommands()
        self.HookCommand(self.OnViewBrowse, win32ui.ID_VIEW_BROWSE)
        self.HookCommand(self.OnFileImport, win32ui.ID_FILE_IMPORT)
        self.HookCommand(self.OnFileCheck, win32ui.ID_FILE_CHECK)
        self.HookCommandUpdate(self.OnUpdateFileCheck, win32ui.ID_FILE_CHECK)
        self.HookCommand(self.OnFileRun, win32ui.ID_FILE_RUN)
        self.HookCommand(self.OnFileLocate, win32ui.ID_FILE_LOCATE)
        self.HookCommand(self.OnInteractiveWindow, win32ui.ID_VIEW_INTERACTIVE)
        self.HookCommandUpdate(
            self.OnUpdateInteractiveWindow, win32ui.ID_VIEW_INTERACTIVE
        )
        self.HookCommand(self.OnViewOptions, win32ui.ID_VIEW_OPTIONS)
        self.HookCommand(self.OnHelpIndex, afxres.ID_HELP_INDEX)
        self.HookCommand(self.OnFileSaveAll, win32ui.ID_FILE_SAVE_ALL)
        self.HookCommand(self.OnViewToolbarDbg, win32ui.ID_VIEW_TOOLBAR_DBG)
        self.HookCommandUpdate(self.OnUpdateViewToolbarDbg, win32ui.ID_VIEW_TOOLBAR_DBG)

    def CreateMainFrame(self):
        return MainFrame()

    def MakeExistingDDEConnection(self):
        # 037826.python.intpyapp.line151.comment Use DDE to connect to an existing instance
        # 037827.python.intpyapp.line152.comment Return None if no existing instance
        try:
            from . import intpydde
        except ImportError:
            # 037828.python.intpyapp.line156.comment No dde support!
            return None
        conv = intpydde.CreateConversation(self.ddeServer)
        try:
            conv.ConnectTo("Pythonwin", "System")
            return conv
        except intpydde.error:
            return None

    def InitDDE(self):
        # 037829.python.intpyapp.line166.comment Do all the magic DDE handling.
        # 037830.python.intpyapp.line167.comment Returns TRUE if we have pumped the arguments to our
        # 037831.python.intpyapp.line168.comment remote DDE app, and we should terminate.
        try:
            from . import intpydde
        except ImportError:
            self.ddeServer = None
            intpydde = None
        if intpydde is not None:
            self.ddeServer = intpydde.DDEServer(self)
            self.ddeServer.Create("Pythonwin", intpydde.CBF_FAIL_SELFCONNECTIONS)
            try:
                # 037832.python.intpyapp.line178.comment If there is an existing instance, pump the arguments to it.
                connection = self.MakeExistingDDEConnection()
                if connection is not None:
                    connection.Exec("self.Activate()")
                    if self.ProcessArgs(sys.argv, connection) is None:
                        return 1
            except:
                # 037833.python.intpyapp.line185.comment It is too early to 'print' an exception - we
                # 037834.python.intpyapp.line186.comment don't have stdout setup yet!
                win32ui.DisplayTraceback(
                    sys.exc_info(), " - error in DDE conversation with Pythonwin"
                )
                return 1

    def InitInstance(self):
        # 037835.python.intpyapp.line193.comment Allow "/nodde" and "/new" to optimize this!
        if (
            "/nodde" not in sys.argv
            and "/new" not in sys.argv
            and "-nodde" not in sys.argv
            and "-new" not in sys.argv
        ):
            if self.InitDDE():
                return 1  # A remote DDE client is doing it for us!
        else:
            self.ddeServer = None

        win32ui.SetRegistryKey(
            f"Python {sys.winver}"
        )  # MFC automatically puts the main frame caption on!
        app.CApp.InitInstance(self)

        # 037838.python.intpyapp.line210.comment Create the taskbar icon
        win32ui.CreateDebuggerThread()

        # 037839.python.intpyapp.line213.comment Allow Pythonwin to host OCX controls.
        win32ui.EnableControlContainer()

        # 037840.python.intpyapp.line216.comment Display the interactive window if the user wants it.
        from . import interact

        interact.CreateInteractiveWindowUserPreference()

        # 037841.python.intpyapp.line221.comment Load the modules we use internally.
        self.LoadSystemModules()

        # 037842.python.intpyapp.line224.comment Load additional module the user may want.
        self.LoadUserModules()

        # 037843.python.intpyapp.line227.comment Load the ToolBar state near the end of the init process, as
        # 037844.python.intpyapp.line228.comment there may be Toolbar IDs created by the user or other modules.
        # 037845.python.intpyapp.line229.comment By now all these modules should be loaded, so all the toolbar IDs loaded.
        try:
            self.frame.LoadBarState("ToolbarDefault")
        except win32ui.error:
            # 037846.python.intpyapp.line233.comment MFC sucks.  It does essentially "GetDlgItem(x)->Something", so if the
            # 037847.python.intpyapp.line234.comment toolbar with ID x does not exist, MFC crashes!  Pythonwin has a trap for this
            # 037848.python.intpyapp.line235.comment but I need to investigate more how to prevent it (AFAIK, ensuring all the
            # 037849.python.intpyapp.line236.comment toolbars are created by now _should_ stop it!)
            pass

        # 037850.python.intpyapp.line239.comment Finally process the command line arguments.
        try:
            self.ProcessArgs(sys.argv)
        except:
            # 037851.python.intpyapp.line243.comment too early for printing anything.
            win32ui.DisplayTraceback(
                sys.exc_info(), " - error processing command line args"
            )

    def ExitInstance(self):
        win32ui.DestroyDebuggerThread()
        try:
            from . import interact

            interact.DestroyInteractiveWindow()
        except:
            pass
        if self.ddeServer is not None:
            self.ddeServer.Shutdown()
            self.ddeServer = None
        return app.CApp.ExitInstance(self)

    def Activate(self):
        # 037852.python.intpyapp.line262.comment Bring to the foreground.  Mainly used when another app starts up, it asks
        # 037853.python.intpyapp.line263.comment this one to activate itself, then it terminates.
        frame = win32ui.GetMainFrame()
        frame.SetForegroundWindow()
        if frame.GetWindowPlacement()[1] == win32con.SW_SHOWMINIMIZED:
            frame.ShowWindow(win32con.SW_RESTORE)

    def ProcessArgs(self, args, dde=None):
        # 037854.python.intpyapp.line270.comment If we are going to talk to a remote app via DDE, then
        # 037855.python.intpyapp.line271.comment activate it!
        if (
            len(args) < 1 or not args[0]
        ):  # argv[0]=='' when started without args, just like Python.exe!
            return

        i = 0
        while i < len(args):
            argType = args[i]
            i += 1
            if argType.startswith("-"):
                # 037857.python.intpyapp.line282.comment Support dash options. Slash options are misinterpreted by python init
                # 037858.python.intpyapp.line283.comment as path and not finding usually 'C:\\' ends up in sys.path[0]
                argType = "/" + argType[1:]
            if not argType.startswith("/"):
                argType = win32ui.GetProfileVal(
                    "Python", "Default Arg Type", "/edit"
                ).lower()
                i -= 1  #  arg is /edit's parameter
            par = i < len(args) and args[i] or "MISSING"
            if argType in ("/nodde", "/new", "-nodde", "-new"):
                # 037860.python.intpyapp.line292.comment Already handled
                pass
            elif argType.startswith("/goto:"):
                gotoline = int(argType[len("/goto:") :])
                if dde:
                    dde.Exec(
                        "from pywin.framework import scriptutils\n"
                        "ed = scriptutils.GetActiveEditControl()\n"
                        "if ed: ed.SetSel(ed.LineIndex(%s - 1))" % gotoline
                    )
                else:
                    from . import scriptutils

                    ed = scriptutils.GetActiveEditControl()
                    if ed:
                        ed.SetSel(ed.LineIndex(gotoline - 1))
            elif argType == "/edit":
                # 037861.python.intpyapp.line309.comment Load up the default application.
                i += 1
                fname = win32api.GetFullPathName(par)
                if not os.path.isfile(fname):
                    # 037862.python.intpyapp.line313.comment if we don't catch this, OpenDocumentFile() (actually
                    # 037863.python.intpyapp.line314.comment PyCDocument.SetPathName() in
                    # 037864.python.intpyapp.line315.comment pywin.scintilla.document.CScintillaDocument.OnOpenDocument)
                    # 037865.python.intpyapp.line316.comment segfaults Pythonwin on recent PY3 builds (b228)
                    win32ui.MessageBox(
                        "No such file: {}\n\nCommand Line: {}".format(
                            fname, win32api.GetCommandLine()
                        ),
                        "Open file for edit",
                        win32con.MB_ICONERROR,
                    )
                    continue
                if dde:
                    dde.Exec(f"win32ui.GetApp().OpenDocumentFile({fname!r})")
                else:
                    win32ui.GetApp().OpenDocumentFile(par)
            elif argType == "/rundlg":
                if dde:
                    dde.Exec(
                        "from pywin.framework import scriptutils;scriptutils.RunScript({!r}, {!r}, 1)".format(
                            par, " ".join(args[i + 1 :])
                        )
                    )
                else:
                    from . import scriptutils

                    scriptutils.RunScript(par, " ".join(args[i + 1 :]))
                return
            elif argType == "/run":
                if dde:
                    dde.Exec(
                        "from pywin.framework import scriptutils;scriptutils.RunScript({!r}, {!r}, 0)".format(
                            par, " ".join(args[i + 1 :])
                        )
                    )
                else:
                    from . import scriptutils

                    scriptutils.RunScript(par, " ".join(args[i + 1 :]), 0)
                return
            elif argType == "/app":
                raise RuntimeError(
                    "/app only supported for new instances of Pythonwin.exe"
                )
            elif argType == "/dde":  # Send arbitary command
                if dde is not None:
                    dde.Exec(par)
                else:
                    win32ui.MessageBox(
                        "The /dde command can only be used\r\nwhen Pythonwin is already running"
                    )
                i += 1
            else:
                raise ValueError("Command line argument not recognised: %s" % argType)

    def LoadSystemModules(self):
        self.DoLoadModules("pywin.framework.editor,pywin.framework.stdin")

    def LoadUserModules(self, moduleNames=None):
        # 037867.python.intpyapp.line372.comment Load the users modules.
        if moduleNames is None:
            default = "pywin.framework.sgrepmdi"
            moduleNames = win32ui.GetProfileVal("Python", "Startup Modules", default)
        self.DoLoadModules(moduleNames)

    def DoLoadModules(self, moduleNames):  # ", sep string of module names.
        if not moduleNames:
            return
        modules = moduleNames.split(",")
        for module in modules:
            try:
                __import__(module)
            except:  # Catch em all, else the app itself dies! 'ImportError:
                traceback.print_exc()
                msg = 'Startup import of user module "%s" failed' % module
                print(msg)
                win32ui.MessageBox(msg)

    # 037870.python.intpyapp.line391.comment
    # 037871.python.intpyapp.line392.comment DDE Callback
    # 037872.python.intpyapp.line393.comment
    def OnDDECommand(self, command):
        try:
            exec(command + "\n")
        except:
            print("ERROR executing DDE command: ", command)
            traceback.print_exc()
            raise

    # 037873.python.intpyapp.line402.comment
    # 037874.python.intpyapp.line403.comment General handlers
    # 037875.python.intpyapp.line404.comment
    def OnViewBrowse(self, id, code):
        "Called when ViewBrowse message is received"
        from pywin.tools import browser

        obName = dialog.GetSimpleInput("Object", "__builtins__", "Browse Python Object")
        if obName is None:
            return
        try:
            browser.Browse(eval(obName, __main__.__dict__, __main__.__dict__))
        except NameError:
            win32ui.MessageBox("This is no object with this name")
        except AttributeError:
            win32ui.MessageBox("The object has no attribute of that name")
        except:
            traceback.print_exc()
            win32ui.MessageBox("This object can not be browsed")

    def OnFileImport(self, id, code):
        "Called when a FileImport message is received. Import the current or specified file"
        from . import scriptutils

        scriptutils.ImportFile()

    def OnFileCheck(self, id, code):
        "Called when a FileCheck message is received. Check the current file."
        from . import scriptutils

        scriptutils.CheckFile()

    def OnUpdateFileCheck(self, cmdui):
        from . import scriptutils

        cmdui.Enable(scriptutils.GetActiveFileName(0) is not None)

    def OnFileRun(self, id, code):
        "Called when a FileRun message is received."
        from . import scriptutils

        showDlg = win32api.GetKeyState(win32con.VK_SHIFT) >= 0
        scriptutils.RunScript(None, None, showDlg)

    def OnFileLocate(self, id, code):
        from . import scriptutils

        global lastLocateFileName  # save the new version away for next time...

        name = dialog.GetSimpleInput(
            "File name", lastLocateFileName, "Locate Python File"
        )
        if name is None:  # Cancelled.
            return
        lastLocateFileName = name
        # 037878.python.intpyapp.line457.comment if ".py" supplied, rip it off!
        # 037879.python.intpyapp.line458.comment should also check for .pys and .pyw
        if lastLocateFileName[-3:].lower() == ".py":
            lastLocateFileName = lastLocateFileName[:-3]
        lastLocateFileName = lastLocateFileName.replace(".", "\\")
        newName = scriptutils.LocatePythonFile(lastLocateFileName)
        if newName is None:
            win32ui.MessageBox("The file '%s' can not be located" % lastLocateFileName)
        else:
            win32ui.GetApp().OpenDocumentFile(newName)

    # 037880.python.intpyapp.line468.comment Display all the "options" property pages we can find
    def OnViewOptions(self, id, code):
        win32ui.InitRichEdit()
        sheet = dialog.PropertySheet("Pythonwin Options")
        # 037881.python.intpyapp.line472.comment Add property pages we know about that need manual work.
        from pywin.dialogs import ideoptions

        sheet.AddPage(ideoptions.OptionsPropPage())

        from . import toolmenu

        sheet.AddPage(toolmenu.ToolMenuPropPage())

        # 037882.python.intpyapp.line481.comment Get other dynamic pages from templates.
        pages = []
        for template in self.GetDocTemplateList():
            try:
                # 037883.python.intpyapp.line485.comment Don't actually call the function with the exception handler.
                getter = template.GetPythonPropertyPages
            except AttributeError:
                # 037884.python.intpyapp.line488.comment Template does not provide property pages!
                continue
            pages.extend(getter())

        # 037885.python.intpyapp.line492.comment Debugger template goes at the end
        try:
            from pywin.debugger import configui
        except ImportError:
            configui = None
        if configui is not None:
            pages.append(configui.DebuggerOptionsPropPage())
        # 037886.python.intpyapp.line499.comment Now simply add the pages, and display the dialog.
        for page in pages:
            sheet.AddPage(page)

        if sheet.DoModal() == win32con.IDOK:
            win32ui.SetStatusText("Applying configuration changes...", 1)
            win32ui.DoWaitCursor(1)
            # 037887.python.intpyapp.line506.comment Tell every Window in our app that win.ini has changed!
            win32ui.GetMainFrame().SendMessageToDescendants(
                win32con.WM_WININICHANGE, 0, 0
            )
            win32ui.DoWaitCursor(0)

    def OnInteractiveWindow(self, id, code):
        # 037888.python.intpyapp.line513.comment toggle the existing state.
        from . import interact

        interact.ToggleInteractiveWindow()

    def OnUpdateInteractiveWindow(self, cmdui):
        try:
            interact = sys.modules["pywin.framework.interact"]
            state = interact.IsInteractiveWindowVisible()
        except KeyError:  # Interactive module hasn't ever been imported.
            state = 0
        cmdui.Enable()
        cmdui.SetCheck(state)

    def OnFileSaveAll(self, id, code):
        # 037890.python.intpyapp.line528.comment Only attempt to save editor documents.
        from pywin.framework.editor import editorTemplate

        num = 0
        for doc in editorTemplate.GetDocumentList():
            if doc.IsModified() and doc.GetPathName():
                num = num = 1
                doc.OnSaveDocument(doc.GetPathName())
        win32ui.SetStatusText("%d documents saved" % num, 1)

    def OnViewToolbarDbg(self, id, code):
        if code == 0:
            return not win32ui.GetMainFrame().OnBarCheck(id)

    def OnUpdateViewToolbarDbg(self, cmdui):
        win32ui.GetMainFrame().OnUpdateControlBarMenu(cmdui)
        cmdui.Enable(1)

    def OnHelpIndex(self, id, code):
        from . import help

        help.SelectAndRunHelpFile()


thisApp = InteractivePythonApp()
