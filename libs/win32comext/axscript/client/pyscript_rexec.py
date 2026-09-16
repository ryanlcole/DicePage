# 051256.python.pyscript_rexec.line1.comment A version of the ActiveScripting engine that enables rexec support
# 051257.python.pyscript_rexec.line2.comment This version supports hosting by IE - however, due to Python's
# 051258.python.pyscript_rexec.line3.comment rexec module being neither completely trusted nor private, it is
# 051259.python.pyscript_rexec.line4.comment *not* enabled by default.
# 051260.python.pyscript_rexec.line5.comment As of Python 2.2, rexec is simply not available - thus, if you use this,
# 051261.python.pyscript_rexec.line6.comment a HTML page can do almost *anything* at all on your machine.

# 051262.python.pyscript_rexec.line8.comment You almost certainly do NOT want to use this!

import pythoncom
from win32com.axscript import axscript

from . import pyscript

INTERFACE_USES_DISPEX = 0x00000004  # Object knows to use IDispatchEx
INTERFACE_USES_SECURITY_MANAGER = (
    0x00000008  # Object knows to use IInternetHostSecurityManager
)


class PyScriptRExec(pyscript.PyScript):
    # 051265.python.pyscript_rexec.line22.comment Setup the auto-registration stuff...
    _reg_verprogid_ = "Python.AXScript-rexec.2"
    _reg_progid_ = "Python"  # Same ProgID as the standard engine.
    # 051267.python.pyscript_rexec.line25.comment _reg_policy_spec_ = default
    _reg_catids_ = [axscript.CATID_ActiveScript, axscript.CATID_ActiveScriptParse]
    _reg_desc_ = "Python ActiveX Scripting Engine (with rexec support)"
    _reg_clsid_ = "{69c2454b-efa2-455b-988c-c3651c4a2f69}"
    _reg_class_spec_ = "win32com.axscript.client.pyscript_rexec.PyScriptRExec"
    _reg_remove_keys_ = [(".pys",), ("pysFile",)]
    _reg_threading_ = "Apartment"

    def _GetSupportedInterfaceSafetyOptions(self):
        # 051268.python.pyscript_rexec.line34.comment print(
        # 051269.python.pyscript_rexec.line35.comment "**** calling",
        # 051270.python.pyscript_rexec.line36.comment pyscript.PyScript._GetSupportedInterfaceSafetyOptions,
        # 051271.python.pyscript_rexec.line37.comment "**->",
        # 051272.python.pyscript_rexec.line38.comment pyscript.PyScript._GetSupportedInterfaceSafetyOptions(self),
        # 051273.python.pyscript_rexec.line39.comment )
        return (
            INTERFACE_USES_DISPEX
            | INTERFACE_USES_SECURITY_MANAGER
            | axscript.INTERFACESAFE_FOR_UNTRUSTED_DATA
            | axscript.INTERFACESAFE_FOR_UNTRUSTED_CALLER
        )


if __name__ == "__main__":
    print("WARNING: By registering this engine, you are giving remote HTML code")
    print("the ability to execute *any* code on your system.")
    print()
    print("You almost certainly do NOT want to do this.")
    print("You have been warned, and are doing this at your own (significant) risk")
    pyscript.Register(PyScriptRExec)
