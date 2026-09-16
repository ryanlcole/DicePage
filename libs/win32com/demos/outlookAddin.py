# 049474.python.outlookAddin.line1.comment A demo plugin for Microsoft Outlook (NOT Outlook Express)
# 049475.python.outlookAddin.line2.comment
# 049476.python.outlookAddin.line3.comment This addin simply adds a new button to the main Outlook toolbar,
# 049477.python.outlookAddin.line4.comment and displays a message box when clicked.  Thus, it demonstrates
# 049478.python.outlookAddin.line5.comment how to plug in to Outlook itself, and hook outlook events.
# 049479.python.outlookAddin.line6.comment
# 049480.python.outlookAddin.line7.comment Additionally, each time a new message arrives in the Inbox, a message
# 049481.python.outlookAddin.line8.comment is printed with the subject of the message.
# 049482.python.outlookAddin.line9.comment
# 049483.python.outlookAddin.line10.comment To register the addin, simply execute:
# 049484.python.outlookAddin.line11.comment outlookAddin.py
# 049485.python.outlookAddin.line12.comment This will install the COM server, and write the necessary
# 049486.python.outlookAddin.line13.comment AddIn key to Outlook
# 049487.python.outlookAddin.line14.comment
# 049488.python.outlookAddin.line15.comment To unregister completely:
# 049489.python.outlookAddin.line16.comment outlookAddin.py --unregister
# 049490.python.outlookAddin.line17.comment
# 049491.python.outlookAddin.line18.comment To debug, execute:
# 049492.python.outlookAddin.line19.comment outlookAddin.py --debug
# 049493.python.outlookAddin.line20.comment
# 049494.python.outlookAddin.line21.comment Then open Pythonwin, and select "Tools->Trace Collector Debugging Tool"
# 049495.python.outlookAddin.line22.comment Restart Outlook, and you should see some output generated.
# 049496.python.outlookAddin.line23.comment
# 049497.python.outlookAddin.line24.comment NOTE: If the AddIn fails with an error, Outlook will re-register
# 049498.python.outlookAddin.line25.comment the addin to not automatically load next time Outlook starts.  To
# 049499.python.outlookAddin.line26.comment correct this, simply re-register the addin (see above)

import sys

import pythoncom
from win32com import universal
from win32com.client import DispatchWithEvents, constants, gencache

# 049500.python.outlookAddin.line34.comment Support for COM objects we use.
gencache.EnsureModule(
    "{00062FFF-0000-0000-C000-000000000046}", 0, 9, 0, bForDemand=True
)  # Outlook 9
gencache.EnsureModule(
    "{2DF8D04C-5BFA-101B-BDE5-00AA0044DE52}", 0, 2, 1, bForDemand=True
)  # Office 9

# 049503.python.outlookAddin.line42.comment The TLB defining the interfaces we implement
universal.RegisterInterfaces(
    "{AC0714F2-3D04-11D1-AE7D-00A0C90F26F4}", 0, 1, 0, ["_IDTExtensibility2"]
)


class ButtonEvent:
    def OnClick(self, button, cancel):
        import win32ui  # Possible, but not necessary, to use a Pythonwin GUI

        win32ui.MessageBox("Hello from Python")
        return cancel


class FolderEvent:
    def OnItemAdd(self, item):
        try:
            print("An item was added to the inbox with subject:", item.Subject)
        except AttributeError:
            print(f"An item was added to the inbox, but it has no subject! - {item!r}")


class OutlookAddin:
    _com_interfaces_ = ["_IDTExtensibility2"]
    _public_methods_ = []
    _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
    _reg_clsid_ = "{0F47D9F3-598B-4d24-B7E3-92AC15ED27E2}"
    _reg_progid_ = "Python.Test.OutlookAddin"
    _reg_policy_spec_ = "win32com.server.policy.EventHandlerPolicy"

    def OnConnection(self, application, connectMode, addin, custom):
        print("OnConnection", application, connectMode, addin, custom)
        # 049505.python.outlookAddin.line74.comment ActiveExplorer may be none when started without a UI (eg, WinCE synchronisation)
        activeExplorer = application.ActiveExplorer()
        if activeExplorer is not None:
            bars = activeExplorer.CommandBars
            toolbar = bars.Item("Standard")
            item = toolbar.Controls.Add(Type=constants.msoControlButton, Temporary=True)
            # 049506.python.outlookAddin.line80.comment Hook events for the item
            item = self.toolbarButton = DispatchWithEvents(item, ButtonEvent)
            item.Caption = "Python"
            item.TooltipText = "Click for Python"
            item.Enabled = True

        # 049507.python.outlookAddin.line86.comment And now, for the sake of demonstration, setup a hook for all new messages
        inbox = application.Session.GetDefaultFolder(constants.olFolderInbox)
        self.inboxItems = DispatchWithEvents(inbox.Items, FolderEvent)

    def OnDisconnection(self, mode, custom):
        print("OnDisconnection")

    def OnAddInsUpdate(self, custom):
        print("OnAddInsUpdate", custom)

    def OnStartupComplete(self, custom):
        print("OnStartupComplete", custom)

    def OnBeginShutdown(self, custom):
        print("OnBeginShutdown", custom)


def RegisterAddin(klass):
    import winreg

    key = winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Office\\Outlook\\Addins"
    )
    subkey = winreg.CreateKey(key, klass._reg_progid_)
    winreg.SetValueEx(subkey, "CommandLineSafe", 0, winreg.REG_DWORD, 0)
    winreg.SetValueEx(subkey, "LoadBehavior", 0, winreg.REG_DWORD, 3)
    winreg.SetValueEx(subkey, "Description", 0, winreg.REG_SZ, klass._reg_progid_)
    winreg.SetValueEx(subkey, "FriendlyName", 0, winreg.REG_SZ, klass._reg_progid_)


def UnregisterAddin(klass):
    import winreg

    try:
        winreg.DeleteKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Office\\Outlook\\Addins\\" + klass._reg_progid_,
        )
    except OSError:
        pass


if __name__ == "__main__":
    import win32com.server.register

    win32com.server.register.UseCommandLine(OutlookAddin)
    if "--unregister" in sys.argv:
        UnregisterAddin(OutlookAddin)
    else:
        RegisterAddin(OutlookAddin)
