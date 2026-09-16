# -*- coding: latin-1 -*-

# 049415.python.iebutton.line3.comment PyWin32 Internet Explorer Button
# 049416.python.iebutton.line4.comment
# 049417.python.iebutton.line5.comment written by Leonard Ritter (paniq@gmx.net)
# 049418.python.iebutton.line6.comment and Robert Förtsch (info@robert-foertsch.com)


"""
This sample implements a simple IE Button COM server
with access to the IWebBrowser2 interface.

To demonstrate:
* Execute this script to register the server.
* Open Pythonwin's Tools -> Trace Collector Debugging Tool, so you can
  see the output of 'print' statements in this demo.
* Open a new IE instance.  The toolbar should have a new "scissors" icon,
  with tooltip text "IE Button" - this is our new button - click it.
* Switch back to the Pythonwin window - you should see:
   IOleCommandTarget::Exec called.
  This is the button being clicked.  Extending this to do something more
  useful is left as an exercise.

Contribtions to this sample to make it a little "friendlier" welcome!
"""

# 049419.python.iebutton.line27.comment imports section

import pythoncom
import win32api
import win32com
import win32com.server.register

# 049420.python.iebutton.line34.comment This demo uses 'print' - use win32traceutil to see it if we have no
# 049421.python.iebutton.line35.comment console.
try:
    win32api.GetConsoleTitle()
except win32api.error:
    import win32traceutil


from win32com.axcontrol import axcontrol

# 049422.python.iebutton.line44.comment ensure we know the ms internet controls typelib so we have access to IWebBrowser2 later on
win32com.client.gencache.EnsureModule("{EAB22AC0-30C1-11CF-A7EB-0000C05BAE0B}", 0, 1, 1)


# 049423.python.iebutton.line48.comment
IObjectWithSite_methods = ["SetSite", "GetSite"]
IOleCommandTarget_methods = ["Exec", "QueryStatus"]

_iebutton_methods_ = IOleCommandTarget_methods + IObjectWithSite_methods
_iebutton_com_interfaces_ = [
    axcontrol.IID_IOleCommandTarget,
    axcontrol.IID_IObjectWithSite,  # IObjectWithSite
]


class Stub:
    """
    this class serves as a method stub,
    outputting debug info whenever the object
    is being called.
    """

    def __init__(self, name):
        self.name = name

    def __call__(self, *args):
        print("STUB: ", self.name, args)


class IEButton:
    """
    The actual COM server class
    """

    _com_interfaces_ = _iebutton_com_interfaces_
    _public_methods_ = _iebutton_methods_
    _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
    _button_text_ = "IE Button"
    _tool_tip_ = "An example implementation for an IE Button."
    _icon_ = ""
    _hot_icon_ = ""

    def __init__(self):
        # 049425.python.iebutton.line87.comment put stubs for non-implemented methods
        for method in self._public_methods_:
            if not hasattr(self, method):
                print("providing default stub for %s" % method)
                setattr(self, method, Stub(method))

    def QueryStatus(self, pguidCmdGroup, prgCmds, cmdtextf):
        # 049426.python.iebutton.line94.comment 'cmdtextf' is the 'cmdtextf' element from the OLECMDTEXT structure,
        # 049427.python.iebutton.line95.comment or None if a NULL pointer was passed.
        result = []
        for id, flags in prgCmds:
            flags |= axcontrol.OLECMDF_SUPPORTED | axcontrol.OLECMDF_ENABLED
            result.append((id, flags))
        if cmdtextf is None:
            cmdtext = None  # must return None if nothing requested.
        # 049429.python.iebutton.line102.comment IE never seems to want any text - this code is here for
        # 049430.python.iebutton.line103.comment demo purposes only
        elif cmdtextf == axcontrol.OLECMDTEXTF_NAME:
            cmdtext = "IEButton Name"
        else:
            cmdtext = "IEButton State"
        return result, cmdtext

    def Exec(self, pguidCmdGroup, nCmdID, nCmdExecOpt, pvaIn):
        print(pguidCmdGroup, nCmdID, nCmdExecOpt, pvaIn)
        print("IOleCommandTarget::Exec called.")
        # 049431.python.iebutton.line113.comment self.webbrowser.ShowBrowserBar(GUID_IETOOLBAR, not is_ietoolbar_visible())

    def SetSite(self, unknown):
        if unknown:
            # 049432.python.iebutton.line117.comment first get a command target
            cmdtarget = unknown.QueryInterface(axcontrol.IID_IOleCommandTarget)
            # 049433.python.iebutton.line119.comment then travel over to a service provider
            serviceprovider = cmdtarget.QueryInterface(pythoncom.IID_IServiceProvider)
            # 049434.python.iebutton.line121.comment finally ask for the internet explorer application, returned as a dispatch object
            self.webbrowser = win32com.client.Dispatch(
                serviceprovider.QueryService(
                    "{0002DF05-0000-0000-C000-000000000046}", pythoncom.IID_IDispatch
                )
            )
        else:
            # 049435.python.iebutton.line128.comment lose all references
            self.webbrowser = None

    def GetClassID(self):
        return self._reg_clsid_


def register(classobj):
    import winreg

    subKeyCLSID = (
        "SOFTWARE\\Microsoft\\Internet Explorer\\Extensions\\%38s"
        % classobj._reg_clsid_
    )
    try:
        hKey = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, subKeyCLSID)
        subKey = winreg.SetValueEx(
            hKey, "ButtonText", 0, winreg.REG_SZ, classobj._button_text_
        )
        winreg.SetValueEx(
            hKey, "ClsidExtension", 0, winreg.REG_SZ, classobj._reg_clsid_
        )  # reg value for calling COM object
        winreg.SetValueEx(
            hKey, "CLSID", 0, winreg.REG_SZ, "{1FBA04EE-3024-11D2-8F1F-0000F87ABD16}"
        )  # CLSID for button that sends command to COM object
        winreg.SetValueEx(hKey, "Default Visible", 0, winreg.REG_SZ, "Yes")
        winreg.SetValueEx(hKey, "ToolTip", 0, winreg.REG_SZ, classobj._tool_tip_)
        winreg.SetValueEx(hKey, "Icon", 0, winreg.REG_SZ, classobj._icon_)
        winreg.SetValueEx(hKey, "HotIcon", 0, winreg.REG_SZ, classobj._hot_icon_)
    except OSError:
        print("Couldn't set standard toolbar reg keys.")
    else:
        print("Set standard toolbar reg keys.")


def unregister(classobj):
    import winreg

    subKeyCLSID = (
        "SOFTWARE\\Microsoft\\Internet Explorer\\Extensions\\%38s"
        % classobj._reg_clsid_
    )
    try:
        hKey = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, subKeyCLSID)
        subKey = winreg.DeleteValue(hKey, "ButtonText")
        winreg.DeleteValue(hKey, "ClsidExtension")  # for calling COM object
        winreg.DeleteValue(hKey, "CLSID")
        winreg.DeleteValue(hKey, "Default Visible")
        winreg.DeleteValue(hKey, "ToolTip")
        winreg.DeleteValue(hKey, "Icon")
        winreg.DeleteValue(hKey, "HotIcon")
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, subKeyCLSID)
    except OSError:
        print("Couldn't delete Standard toolbar regkey.")
    else:
        print("Deleted Standard toolbar regkey.")


# 049439.python.iebutton.line186.comment
# 049440.python.iebutton.line187.comment test implementation
# 049441.python.iebutton.line188.comment


class PyWin32InternetExplorerButton(IEButton):
    _reg_clsid_ = "{104B66A9-9E68-49D1-A3F5-94754BE9E0E6}"
    _reg_progid_ = "PyWin32.IEButton"
    _reg_desc_ = "Test Button"
    _button_text_ = "IE Button"
    _tool_tip_ = "An example implementation for an IE Button."
    _icon_ = ""
    _hot_icon_ = _icon_


def DllRegisterServer():
    register(PyWin32InternetExplorerButton)


def DllUnregisterServer():
    unregister(PyWin32InternetExplorerButton)


if __name__ == "__main__":
    win32com.server.register.UseCommandLine(
        PyWin32InternetExplorerButton,
        finalize_register=DllRegisterServer,
        finalize_unregister=DllUnregisterServer,
    )
