# 021628.python.extension_simple.line1.comment This is an ISAPI extension purely for testing purposes.  It is NOT
# 021629.python.extension_simple.line2.comment a 'demo' (even though it may be useful!)
# 021630.python.extension_simple.line3.comment
# 021631.python.extension_simple.line4.comment Install this extension, then point your browser to:
# 021632.python.extension_simple.line5.comment "http://localhost/pyisapi_test/test1"
# 021633.python.extension_simple.line6.comment This will execute the method 'test1' below.  See below for the list of
# 021634.python.extension_simple.line7.comment test methods that are acceptable.

# 021635.python.extension_simple.line9.comment If we have no console (eg, am running from inside IIS), redirect output
# 021636.python.extension_simple.line10.comment somewhere useful - in this case, the standard win32 trace collector.
import win32api
import winerror

from isapi import ExtensionError, threaded_extension

try:
    win32api.GetConsoleTitle()
except win32api.error:
    # 021637.python.extension_simple.line19.comment No console - redirect
    import win32traceutil


# 021638.python.extension_simple.line23.comment The ISAPI extension - handles requests in our virtual dir, and sends the
# 021639.python.extension_simple.line24.comment response to the client.
class Extension(threaded_extension.ThreadPoolExtension):
    "Python ISAPI Tester"

    def Dispatch(self, ecb):
        print('Tester dispatching "{}"'.format(ecb.GetServerVariable("URL")))
        url = ecb.GetServerVariable("URL")
        test_name = url.split("/")[-1]
        meth = getattr(self, test_name, None)
        if meth is None:
            raise AttributeError(f"No test named '{test_name}'")
        result = meth(ecb)
        if result is None:
            # 021640.python.extension_simple.line37.comment This means the test finalized everything
            return
        ecb.SendResponseHeaders("200 OK", "Content-type: text/html\r\n\r\n", False)
        print("<HTML><BODY>Finished running test <i>", test_name, "</i>", file=ecb)
        print("<pre>", file=ecb)
        print(result, file=ecb)
        print("</pre>", file=ecb)
        print("</BODY></HTML>", file=ecb)
        ecb.DoneWithSession()

    def test1(self, ecb):
        try:
            ecb.GetServerVariable("foo bar")
            raise AssertionError("should have failed!")
        except ExtensionError as err:
            assert err.errno == winerror.ERROR_INVALID_INDEX, err
        return "worked!"

    def test_long_vars(self, ecb):
        qs = ecb.GetServerVariable("QUERY_STRING")
        # 021641.python.extension_simple.line57.comment Our implementation has a default buffer size of 8k - so we test
        # 021642.python.extension_simple.line58.comment the code that handles an overflow by ensuring there are more
        # 021643.python.extension_simple.line59.comment than 8k worth of chars in the URL.
        expected_query = "x" * 8500
        if len(qs) == 0:
            # 021644.python.extension_simple.line62.comment Just the URL with no query part - redirect to myself, but with
            # 021645.python.extension_simple.line63.comment a huge query portion.
            me = ecb.GetServerVariable("URL")
            headers = "Location: " + me + "?" + expected_query + "\r\n\r\n"
            ecb.SendResponseHeaders("301 Moved", headers)
            ecb.DoneWithSession()
            return None
        if qs == expected_query:
            return "Total length of variable is %d - test worked!" % (len(qs),)
        else:
            return "Unexpected query portion!  Got %d chars, expected %d" % (
                len(qs),
                len(expected_query),
            )

    def test_unicode_vars(self, ecb):
        # 021646.python.extension_simple.line78.comment We need to check that we are running IIS6!  This seems the only
        # 021647.python.extension_simple.line79.comment effective way from an extension.
        ver = float(ecb.GetServerVariable("SERVER_SOFTWARE").split("/")[1])
        if ver < 6.0:
            return "This is IIS version %g - unicode only works in IIS6 and later" % ver

        us = ecb.GetServerVariable("UNICODE_SERVER_NAME")
        assert isinstance(us, str), "unexpected type!"
        assert us == str(ecb.GetServerVariable("SERVER_NAME")), (
            "Unicode and non-unicode values were not the same"
        )
        return "worked!"


# 021648.python.extension_simple.line92.comment The entry points for the ISAPI extension.
def __ExtensionFactory__():
    return Extension()


if __name__ == "__main__":
    # 021649.python.extension_simple.line98.comment If run from the command-line, install ourselves.
    from isapi.install import *

    params = ISAPIParameters()
    # 021650.python.extension_simple.line102.comment Setup the virtual directories - this is a list of directories our
    # 021651.python.extension_simple.line103.comment extension uses - in this case only 1.
    # 021652.python.extension_simple.line104.comment Each extension has a "script map" - this is the mapping of ISAPI
    # 021653.python.extension_simple.line105.comment extensions.
    sm = [ScriptMapParams(Extension="*", Flags=0)]
    vd = VirtualDirParameters(
        Name="pyisapi_test",
        Description=Extension.__doc__,
        ScriptMaps=sm,
        ScriptMapUpdate="replace",
    )
    params.VirtualDirs = [vd]
    HandleCommandLine(params)
