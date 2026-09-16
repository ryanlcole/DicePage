# 021501.python.redirector_asynch.line1.comment This is a sample ISAPI extension written in Python.

# 021502.python.redirector_asynch.line3.comment This is like the other 'redirector' samples, but uses asnch IO when writing
# 021503.python.redirector_asynch.line4.comment back to the client (it does *not* use asynch io talking to the remote
# 021504.python.redirector_asynch.line5.comment server!)

import sys
import urllib.error
import urllib.parse
import urllib.request

from isapi import isapicon, threaded_extension

# 021505.python.redirector_asynch.line14.comment sys.isapidllhandle will exist when we are loaded by the IIS framework.
# 021506.python.redirector_asynch.line15.comment In this case we redirect our output to the win32traceutil collector.
if hasattr(sys, "isapidllhandle"):
    import win32traceutil

# 021507.python.redirector_asynch.line19.comment The site we are proxying.
proxy = "https://www.python.org"

# 021508.python.redirector_asynch.line22.comment We synchronously read chunks of this size then asynchronously write them.
CHUNK_SIZE = 8192


# 021509.python.redirector_asynch.line26.comment The callback made when IIS completes the asynch write.
def io_callback(ecb, fp, cbIO, errcode):
    print("IO callback", ecb, fp, cbIO, errcode)
    chunk = fp.read(CHUNK_SIZE)
    if chunk:
        ecb.WriteClient(chunk, isapicon.HSE_IO_ASYNC)
        # 021510.python.redirector_asynch.line32.comment and wait for the next callback to say this chunk is done.
    else:
        # 021511.python.redirector_asynch.line34.comment eof - say we are complete.
        fp.close()
        ecb.DoneWithSession()


# 021512.python.redirector_asynch.line39.comment The ISAPI extension - handles all requests in the site.
class Extension(threaded_extension.ThreadPoolExtension):
    "Python sample proxy server - asynch version."

    def Dispatch(self, ecb):
        print('IIS dispatching "{}"'.format(ecb.GetServerVariable("URL")))
        url = ecb.GetServerVariable("URL")

        new_url = proxy + url
        print("Opening %s" % new_url)
        fp = urllib.request.urlopen(new_url)
        headers = fp.info()
        ecb.SendResponseHeaders("200 OK", str(headers) + "\r\n", False)
        # 021513.python.redirector_asynch.line52.comment now send the first chunk asynchronously
        ecb.ReqIOCompletion(io_callback, fp)
        chunk = fp.read(CHUNK_SIZE)
        if chunk:
            ecb.WriteClient(chunk, isapicon.HSE_IO_ASYNC)
            return isapicon.HSE_STATUS_PENDING
        # 021514.python.redirector_asynch.line58.comment no data - just close things now.
        ecb.DoneWithSession()
        return isapicon.HSE_STATUS_SUCCESS


# 021515.python.redirector_asynch.line63.comment The entry points for the ISAPI extension.
def __ExtensionFactory__():
    return Extension()


if __name__ == "__main__":
    # 021516.python.redirector_asynch.line69.comment If run from the command-line, install ourselves.
    from isapi.install import *

    params = ISAPIParameters()
    # 021517.python.redirector_asynch.line73.comment Setup the virtual directories - this is a list of directories our
    # 021518.python.redirector_asynch.line74.comment extension uses - in this case only 1.
    # 021519.python.redirector_asynch.line75.comment Each extension has a "script map" - this is the mapping of ISAPI
    # 021520.python.redirector_asynch.line76.comment extensions.
    sm = [ScriptMapParams(Extension="*", Flags=0)]
    vd = VirtualDirParameters(
        Name="/",
        Description=Extension.__doc__,
        ScriptMaps=sm,
        ScriptMapUpdate="replace",
    )
    params.VirtualDirs = [vd]
    HandleCommandLine(params)
