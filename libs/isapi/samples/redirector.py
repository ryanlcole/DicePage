# 021463.python.redirector.line1.comment This is a sample ISAPI extension written in Python.
# 021464.python.redirector.line2.comment
# 021465.python.redirector.line3.comment Please see README.txt in this directory, and specifically the
# 021466.python.redirector.line4.comment information about the "loader" DLL - installing this sample will create
# 021467.python.redirector.line5.comment "_redirector.dll" in the current directory.  The readme explains this.

# 021468.python.redirector.line7.comment Executing this script (or any server config script) will install the extension
# 021469.python.redirector.line8.comment into your web server. As the server executes, the PyISAPI framework will load
# 021470.python.redirector.line9.comment this module and create your Extension and Filter objects.

# 021471.python.redirector.line11.comment This is the simplest possible redirector (or proxy) we can write.  The
# 021472.python.redirector.line12.comment extension installs with a mask of '*' in the root of the site.
# 021473.python.redirector.line13.comment As an added bonus though, we optionally show how, on IIS6 and later, we
# 021474.python.redirector.line14.comment can use HSE_ERQ_EXEC_URL to ignore certain requests - in IIS5 and earlier
# 021475.python.redirector.line15.comment we can only do this with an ISAPI filter - see redirector_with_filter for
# 021476.python.redirector.line16.comment an example.  If this sample is run on IIS5 or earlier it simply ignores
# 021477.python.redirector.line17.comment any excludes.

import sys
from urllib.request import urlopen

import win32api

from isapi import isapicon, threaded_extension

# 021478.python.redirector.line26.comment sys.isapidllhandle will exist when we are loaded by the IIS framework.
# 021479.python.redirector.line27.comment In this case we redirect our output to the win32traceutil collector.
if hasattr(sys, "isapidllhandle"):
    import win32traceutil

# 021480.python.redirector.line31.comment The site we are proxying.
proxy = "https://www.python.org"

# 021481.python.redirector.line34.comment Urls we exclude (ie, allow IIS to handle itself) - all are lowered,
# 021482.python.redirector.line35.comment and these entries exist by default on Vista...
excludes = ["/iisstart.htm", "/welcome.png"]


# 021483.python.redirector.line39.comment An "io completion" function, called when ecb.ExecURL completes...
def io_callback(ecb, url, cbIO, errcode):
    # 021484.python.redirector.line41.comment Get the status of our ExecURL
    httpstatus, substatus, win32 = ecb.GetExecURLStatus()
    print(
        "ExecURL of %r finished with http status %d.%d, win32 status %d (%s)"
        % (url, httpstatus, substatus, win32, win32api.FormatMessage(win32).strip())
    )
    # 021485.python.redirector.line47.comment nothing more to do!
    ecb.DoneWithSession()


# 021486.python.redirector.line51.comment The ISAPI extension - handles all requests in the site.
class Extension(threaded_extension.ThreadPoolExtension):
    "Python sample Extension"

    def Dispatch(self, ecb):
        # 021487.python.redirector.line56.comment Note that our ThreadPoolExtension base class will catch exceptions
        # 021488.python.redirector.line57.comment in our Dispatch method, and write the traceback to the client.
        # 021489.python.redirector.line58.comment That is perfect for this sample, so we don't catch our own.
        # 021490.python.redirector.line59.comment print(f'IIS dispatching "{ecb.GetServerVariable("URL")}"')
        url = ecb.GetServerVariable("URL").decode("ascii")
        for exclude in excludes:
            if url.lower().startswith(exclude):
                print("excluding %s" % url)
                if ecb.Version < 0x60000:
                    print("(but this is IIS5 or earlier - can't do 'excludes')")
                else:
                    ecb.IOCompletion(io_callback, url)
                    ecb.ExecURL(
                        None,
                        None,
                        None,
                        None,
                        None,
                        isapicon.HSE_EXEC_URL_IGNORE_CURRENT_INTERCEPTOR,
                    )
                    return isapicon.HSE_STATUS_PENDING

        new_url = proxy + url
        print("Opening %s" % new_url)
        fp = urlopen(new_url)
        headers = fp.info()
        # 021491.python.redirector.line82.comment subtle breakage: str(headers) normalizes \r\n
        # 021492.python.redirector.line83.comment back to \n and also sticks an extra \n term.
        # 021493.python.redirector.line84.comment take *all* trailing \n off, replace remaining with
        # 021494.python.redirector.line85.comment \r\n, then add the 2 trailing \r\n.
        header_text = str(headers).rstrip("\n").replace("\n", "\r\n") + "\r\n\r\n"
        ecb.SendResponseHeaders("200 OK", header_text, False)
        ecb.WriteClient(fp.read())
        ecb.DoneWithSession()
        print(f"Returned data from '{new_url}'")
        return isapicon.HSE_STATUS_SUCCESS


# 021495.python.redirector.line94.comment The entry points for the ISAPI extension.
def __ExtensionFactory__():
    return Extension()


if __name__ == "__main__":
    # 021496.python.redirector.line100.comment If run from the command-line, install ourselves.
    from isapi.install import *

    params = ISAPIParameters()
    # 021497.python.redirector.line104.comment Setup the virtual directories - this is a list of directories our
    # 021498.python.redirector.line105.comment extension uses - in this case only 1.
    # 021499.python.redirector.line106.comment Each extension has a "script map" - this is the mapping of ISAPI
    # 021500.python.redirector.line107.comment extensions.
    sm = [ScriptMapParams(Extension="*", Flags=0)]
    vd = VirtualDirParameters(
        Name="/",
        Description=Extension.__doc__,
        ScriptMaps=sm,
        ScriptMapUpdate="replace",
    )
    params.VirtualDirs = [vd]
    HandleCommandLine(params)
