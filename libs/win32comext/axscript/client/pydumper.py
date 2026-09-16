# 051191.python.pydumper.line1.comment pydumper.py
# 051192.python.pydumper.line2.comment
# 051193.python.pydumper.line3.comment This is being worked on - it does not yet work at all, in ay way
# 051194.python.pydumper.line4.comment shape or form :-)
# 051195.python.pydumper.line5.comment
# 051196.python.pydumper.line6.comment A new script engine, derived from the standard scripting engine,
# 051197.python.pydumper.line7.comment which dumps information.

# 051198.python.pydumper.line9.comment This generally can be used to grab all sorts of useful details about
# 051199.python.pydumper.line10.comment an engine - expose bugs in it or Python, dump the object model, etc.

# 051200.python.pydumper.line12.comment As it is derived from the standard engine, it fully supports Python
# 051201.python.pydumper.line13.comment as a scripting language - meaning the dumps produced can be quite dynamic,
# 051202.python.pydumper.line14.comment and based on the script code you execute.

import sys

import win32api
import win32con
from win32com.axscript import axscript

from . import pyscript

PyDump_CLSID = "{ac527e60-c693-11d0-9c25-00aa00125a98}"


class AXScriptAttribute(pyscript.AXScriptAttribute):
    pass


class NamedScriptAttribute(pyscript.NamedScriptAttribute):
    pass


class PyScript(pyscript.PyScript):
    pass


def Register():
    if "-d" in sys.argv:
        dispatcher = "DispatcherWin32trace"
        debug_desc = " (" + dispatcher + ")"
        debug_option = "Yes"
    else:
        dispatcher = None
        debug_desc = ""
        debug_option = ""

    categories = [axscript.CATID_ActiveScript, axscript.CATID_ActiveScriptParse]
    clsid = PyDump_CLSID
    lcid = 0x0409  # // english
    policy = None  # "win32com.axscript.client.axspolicy.AXScriptPolicy"

    print("Registering COM server%s..." % debug_desc)
    from win32com.server.register import RegisterServer, _set_string

    languageName = "PyDump"
    verProgId = "Python.Dumper.1"
    RegisterServer(
        clsid=clsid,
        pythonInstString="win32com.axscript.client.pyscript.PyDumper",
        desc="Python Debugging/Dumping ActiveX Scripting Engine",
        progID=languageName,
        verProgID=verProgId,
        policy=policy,
        catids=categories,
        dispatcher=dispatcher,
    )

    win32api.RegCreateKey(win32con.HKEY_CLASSES_ROOT, languageName + "\\OLEScript")
    # 051205.python.pydumper.line71.comment Basic Registration for wsh.
    _set_string(".pysDump", "pysDumpFile")
    _set_string("pysDumpFile\\ScriptEngine", languageName)
    print("Dumping Server registered.")


if __name__ == "__main__":
    Register()
