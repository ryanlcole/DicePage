import sys

import pythoncom
import pywintypes
from win32com.axscript import axscript
from win32com.axscript.server import axsite
from win32com.server import connect, util


class MySite(axsite.AXSite):
    def OnScriptError(self, error):
        exc = error.GetExceptionInfo()
        context, line, char = error.GetSourcePosition()
        print(" >Exception:", exc[1])
        try:
            st = error.GetSourceLineText()
        except pythoncom.com_error:
            st = None
        if st is None:
            st = ""
        text = st + "\n" + (" " * (char - 1)) + "^" + "\n" + exc[2]
        for line in text.splitlines():
            print("  >" + line)


class MyCollection(util.Collection):
    def _NewEnum(self):
        print("Making new Enumerator")
        return util.Collection._NewEnum(self)


class Test:
    _public_methods_ = ["echo"]
    _public_attrs_ = ["collection", "verbose"]

    def __init__(self):
        self.verbose = 0
        self.collection = util.wrap(MyCollection([1, "Two", 3]))
        self.last = ""

    # 051289.python.leakTest.line41.comment self._connect_server_ = TestConnectServer(self)

    def echo(self, *args):
        self.last = "".join(map(str, args))
        if self.verbose:
            for arg in args:
                print(arg, end=" ")
            print()


# 051290.python.leakTest.line51.comment self._connect_server_.Broadcast(last)


# 051291.python.leakTest.line54.comment ### Connections currently won't work, as there is no way for the engine to
# 051292.python.leakTest.line55.comment ### know what events we support.  We need typeinfo support.

IID_ITestEvents = pywintypes.IID("{8EB72F90-0D44-11d1-9C4B-00AA00125A98}")


class TestConnectServer(connect.ConnectableServer):
    _connect_interfaces_ = [IID_ITestEvents]

    # 051293.python.leakTest.line63.comment The single public method that the client can call on us
    # 051294.python.leakTest.line64.comment (ie, as a normal COM server, this exposes just this single method.
    def __init__(self, object):
        self.object = object

    def Broadcast(self, arg):
        # 051295.python.leakTest.line69.comment Simply broadcast a notification.
        self._BroadcastNotify(self.NotifyDoneIt, (arg,))

    def NotifyDoneIt(self, interface, arg):
        interface.Invoke(1000, 0, pythoncom.DISPATCH_METHOD, 1, arg)


VBScript = """\
prop = "Property Value"

sub hello(arg1)
   test.echo arg1
end sub

sub testcollection
   test.verbose = 1
   for each item in test.collection
     test.echo "Collection item is", item
   next
end sub
"""

PyScript = """\
print("PyScript is being parsed...")\n

prop = "Property Value"
def hello(arg1):
   test.echo(arg1)
   pass

def testcollection():
   test.verbose = 1
#   test.collection[1] = "New one"
   for item in test.collection:
     test.echo("Collection item is", item)
   pass
"""

ErrScript = """\
bad code for everyone!
"""


def TestEngine(engineName, code, bShouldWork=1):
    echoer = Test()
    model = {
        "test": util.wrap(echoer),
    }

    site = MySite(model)
    engine = site._AddEngine(engineName)
    engine.AddCode(code, axscript.SCRIPTTEXT_ISPERSISTENT)
    try:
        engine.Start()
    finally:
        if not bShouldWork:
            engine.Close()
            return
    doTestEngine(engine, echoer)
    # 051296.python.leakTest.line128.comment re-transition the engine back to the UNINITIALIZED state, a-la ASP.
    engine.eScript.SetScriptState(axscript.SCRIPTSTATE_UNINITIALIZED)
    engine.eScript.SetScriptSite(util.wrap(site))
    print("restarting")
    engine.Start()
    # 051297.python.leakTest.line133.comment all done!
    engine.Close()


def doTestEngine(engine, echoer):
    # 051298.python.leakTest.line138.comment Now call into the scripts IDispatch
    from win32com.client.dynamic import Dispatch

    ob = Dispatch(engine.GetScriptDispatch())
    try:
        ob.hello("Goober")
    except pythoncom.com_error as exc:
        print("***** Calling 'hello' failed", exc)
        return
    if echoer.last != "Goober":
        print(f"***** Function call didnt set value correctly {echoer.last!r}")

    if str(ob.prop) != "Property Value":
        print(f"***** Property Value not correct - {ob.prop!r}")

    ob.testcollection()

    # 051299.python.leakTest.line155.comment Now make sure my engines can evaluate stuff.
    result = engine.eParse.ParseScriptText(
        "1+1", None, None, None, 0, 0, axscript.SCRIPTTEXT_ISEXPRESSION
    )
    if result != 2:
        print("Engine could not evaluate '1+1' - said the result was", result)


def dotestall():
    for i in range(10):
        TestEngine("Python", PyScript)
        print(sys.gettotalrefcount())


# 051300.python.leakTest.line169.comment print("Testing Exceptions")
# 051301.python.leakTest.line170.comment try:
# 051302.python.leakTest.line171.comment TestEngine("Python", ErrScript, 0)
# 051303.python.leakTest.line172.comment except pythoncom.com_error:
# 051304.python.leakTest.line173.comment pass


def testall():
    dotestall()
    pythoncom.CoUninitialize()
    print(
        "AXScript Host worked correctly - %d/%d COM objects left alive."
        % (pythoncom._GetInterfaceCount(), pythoncom._GetGatewayCount())
    )


if __name__ == "__main__":
    testall()
