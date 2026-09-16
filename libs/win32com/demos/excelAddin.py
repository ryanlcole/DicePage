# 049281.python.excelAddin.line1.comment A demo plugin for Microsoft Excel
# 049282.python.excelAddin.line2.comment
# 049283.python.excelAddin.line3.comment This addin simply adds a new button to the main Excel toolbar,
# 049284.python.excelAddin.line4.comment and displays a message box when clicked.  Thus, it demonstrates
# 049285.python.excelAddin.line5.comment how to plug in to Excel itself, and hook Excel events.
# 049286.python.excelAddin.line6.comment
# 049287.python.excelAddin.line7.comment
# 049288.python.excelAddin.line8.comment To register the addin, simply execute:
# 049289.python.excelAddin.line9.comment excelAddin.py
# 049290.python.excelAddin.line10.comment This will install the COM server, and write the necessary
# 049291.python.excelAddin.line11.comment AddIn key to Excel
# 049292.python.excelAddin.line12.comment
# 049293.python.excelAddin.line13.comment To unregister completely:
# 049294.python.excelAddin.line14.comment excelAddin.py --unregister
# 049295.python.excelAddin.line15.comment
# 049296.python.excelAddin.line16.comment To debug, execute:
# 049297.python.excelAddin.line17.comment excelAddin.py --debug
# 049298.python.excelAddin.line18.comment
# 049299.python.excelAddin.line19.comment Then open Pythonwin, and select "Tools->Trace Collector Debugging Tool"
# 049300.python.excelAddin.line20.comment Restart excel, and you should see some output generated.
# 049301.python.excelAddin.line21.comment
# 049302.python.excelAddin.line22.comment NOTE: If the AddIn fails with an error, Excel will re-register
# 049303.python.excelAddin.line23.comment the addin to not automatically load next time Excel starts.  To
# 049304.python.excelAddin.line24.comment correct this, simply re-register the addin (see above)
# 049305.python.excelAddin.line25.comment
# 049306.python.excelAddin.line26.comment Author <ekoome@yahoo.com> Eric Koome
# 049307.python.excelAddin.line27.comment Copyright (c) 2003 Wavecom Inc.  All rights reserved
# 049308.python.excelAddin.line28.comment
# 049309.python.excelAddin.line29.comment Redistribution and use in source and binary forms, with or without
# 049310.python.excelAddin.line30.comment modification, are permitted provided that the following conditions
# 049311.python.excelAddin.line31.comment are met:
# 049312.python.excelAddin.line32.comment
# 049313.python.excelAddin.line33.comment 1. Redistributions of source code must retain the above copyright
# 049314.python.excelAddin.line34.comment notice, this list of conditions and the following disclaimer.
# 049315.python.excelAddin.line35.comment
# 049316.python.excelAddin.line36.comment THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESSED OR IMPLIED
# 049317.python.excelAddin.line37.comment WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# 049318.python.excelAddin.line38.comment OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# 049319.python.excelAddin.line39.comment DISCLAIMED.  IN NO EVENT SHALL ERIC KOOME OR
# 049320.python.excelAddin.line40.comment ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# 049321.python.excelAddin.line41.comment SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# 049322.python.excelAddin.line42.comment LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# 049323.python.excelAddin.line43.comment USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# 049324.python.excelAddin.line44.comment ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# 049325.python.excelAddin.line45.comment OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# 049326.python.excelAddin.line46.comment OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# 049327.python.excelAddin.line47.comment SUCH DAMAGE.

import sys

import pythoncom
from win32com import universal
from win32com.client import DispatchWithEvents, constants, gencache

# 049328.python.excelAddin.line55.comment Support for COM objects we use.
gencache.EnsureModule(
    "{00020813-0000-0000-C000-000000000046}", 0, 1, 3, bForDemand=True
)  # Excel 9
gencache.EnsureModule(
    "{2DF8D04C-5BFA-101B-BDE5-00AA0044DE52}", 0, 2, 1, bForDemand=True
)  # Office 9

# 049331.python.excelAddin.line63.comment The TLB defining the interfaces we implement
universal.RegisterInterfaces(
    "{AC0714F2-3D04-11D1-AE7D-00A0C90F26F4}", 0, 1, 0, ["_IDTExtensibility2"]
)


class ButtonEvent:
    def OnClick(self, button, cancel):
        import win32con  # Possible, but not necessary, to use a Pythonwin GUI
        import win32ui

        win32ui.MessageBox("Hello from Python", "Python Test", win32con.MB_OKCANCEL)
        return cancel


class ExcelAddin:
    _com_interfaces_ = ["_IDTExtensibility2"]
    _public_methods_ = []
    _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
    _reg_clsid_ = "{C5482ECA-F559-45A0-B078-B2036E6F011A}"
    _reg_progid_ = "Python.Test.ExcelAddin"
    _reg_policy_spec_ = "win32com.server.policy.EventHandlerPolicy"

    def __init__(self):
        self.appHostApp = None

    def OnConnection(self, application, connectMode, addin, custom):
        print("OnConnection", application, connectMode, addin, custom)
        try:
            self.appHostApp = application
            cbcMyBar = self.appHostApp.CommandBars.Add(
                Name="PythonBar",
                Position=constants.msoBarTop,
                MenuBar=constants.msoBarTypeNormal,
                Temporary=True,
            )
            btnMyButton = cbcMyBar.Controls.Add(
                Type=constants.msoControlButton, Parameter="Greetings"
            )
            btnMyButton = self.toolbarButton = DispatchWithEvents(
                btnMyButton, ButtonEvent
            )
            btnMyButton.Style = constants.msoButtonCaption
            btnMyButton.BeginGroup = True
            btnMyButton.Caption = "&Python"
            btnMyButton.TooltipText = "Python rules the World"
            btnMyButton.Width = "34"
            cbcMyBar.Visible = True
        except pythoncom.com_error as xxx_todo_changeme:
            (hr, msg, exc, arg) = xxx_todo_changeme.args
            print("The Excel call failed with code %d: %s" % (hr, msg))
            if exc is None:
                print("There is no extended error information")
            else:
                wcode, source, text, helpFile, helpId, scode = exc
                print("The source of the error is", source)
                print("The error message is", text)
                print("More info can be found in %s (id=%d)" % (helpFile, helpId))

    def OnDisconnection(self, mode, custom):
        print("OnDisconnection")
        self.appHostApp.CommandBars("PythonBar").Delete
        self.appHostApp = None

    def OnAddInsUpdate(self, custom):
        print("OnAddInsUpdate", custom)

    def OnStartupComplete(self, custom):
        print("OnStartupComplete", custom)

    def OnBeginShutdown(self, custom):
        print("OnBeginShutdown", custom)


def RegisterAddin(klass):
    import winreg

    key = winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Office\\Excel\\Addins"
    )
    subkey = winreg.CreateKey(key, klass._reg_progid_)
    winreg.SetValueEx(subkey, "CommandLineSafe", 0, winreg.REG_DWORD, 0)
    winreg.SetValueEx(subkey, "LoadBehavior", 0, winreg.REG_DWORD, 3)
    winreg.SetValueEx(subkey, "Description", 0, winreg.REG_SZ, "Excel Addin")
    winreg.SetValueEx(subkey, "FriendlyName", 0, winreg.REG_SZ, "A Simple Excel Addin")


def UnregisterAddin(klass):
    import winreg

    try:
        winreg.DeleteKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Office\\Excel\\Addins\\" + klass._reg_progid_,
        )
    except OSError:
        pass


if __name__ == "__main__":
    import win32com.server.register

    win32com.server.register.UseCommandLine(ExcelAddin)
    if "--unregister" in sys.argv:
        UnregisterAddin(ExcelAddin)
    else:
        RegisterAddin(ExcelAddin)
