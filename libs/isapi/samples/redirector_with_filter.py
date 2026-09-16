# 021521.python.redirector_with_filter.line1.comment This is a sample configuration file for an ISAPI filter and extension
# 021522.python.redirector_with_filter.line2.comment written in Python.
# 021523.python.redirector_with_filter.line3.comment
# 021524.python.redirector_with_filter.line4.comment Please see README.txt in this directory, and specifically the
# 021525.python.redirector_with_filter.line5.comment information about the "loader" DLL - installing this sample will create
# 021526.python.redirector_with_filter.line6.comment "_redirector_with_filter.dll" in the current directory.  The readme explains
# 021527.python.redirector_with_filter.line7.comment this.

# 021528.python.redirector_with_filter.line9.comment Executing this script (or any server config script) will install the extension
# 021529.python.redirector_with_filter.line10.comment into your web server. As the server executes, the PyISAPI framework will load
# 021530.python.redirector_with_filter.line11.comment this module and create your Extension and Filter objects.

# 021531.python.redirector_with_filter.line13.comment This sample provides sample redirector:
# 021532.python.redirector_with_filter.line14.comment It is implemented by a filter and an extension, so that some requests can
# 021533.python.redirector_with_filter.line15.comment be ignored.  Compare with 'redirector_simple' which avoids the filter, but
# 021534.python.redirector_with_filter.line16.comment is unable to selectively ignore certain requests.
# 021535.python.redirector_with_filter.line17.comment The process is sample uses is:
# 021536.python.redirector_with_filter.line18.comment * The filter is installed globally, as all filters are.
# 021537.python.redirector_with_filter.line19.comment * A Virtual Directory named "python" is setup.  This dir has our ISAPI
# 021538.python.redirector_with_filter.line20.comment extension as the only application, mapped to file-extension '*'.  Thus, our
# 021539.python.redirector_with_filter.line21.comment extension handles *all* requests in this directory.
# 021540.python.redirector_with_filter.line22.comment The basic process is that the filter does URL rewriting, redirecting every
# 021541.python.redirector_with_filter.line23.comment URL to our Virtual Directory.  Our extension then handles this request,
# 021542.python.redirector_with_filter.line24.comment forwarding the data from the proxied site.
# 021543.python.redirector_with_filter.line25.comment For example:
# 021544.python.redirector_with_filter.line26.comment * URL of "index.html" comes in.
# 021545.python.redirector_with_filter.line27.comment * Filter rewrites this to "/python/index.html"
# 021546.python.redirector_with_filter.line28.comment * Our extension sees the full "/python/index.html", removes the leading
# 021547.python.redirector_with_filter.line29.comment portion, and opens and forwards the remote URL.


# 021548.python.redirector_with_filter.line32.comment This sample is very small - it avoid most error handling, etc.  It is for
# 021549.python.redirector_with_filter.line33.comment demonstration purposes only.

import sys
import urllib.error
import urllib.parse
import urllib.request

from isapi import isapicon, threaded_extension
from isapi.simple import SimpleFilter

# 021550.python.redirector_with_filter.line43.comment sys.isapidllhandle will exist when we are loaded by the IIS framework.
# 021551.python.redirector_with_filter.line44.comment In this case we redirect our output to the win32traceutil collector.
if hasattr(sys, "isapidllhandle"):
    import win32traceutil

# 021552.python.redirector_with_filter.line48.comment The site we are proxying.
proxy = "https://www.python.org"
# 021553.python.redirector_with_filter.line50.comment The name of the virtual directory we install in, and redirect from.
virtualdir = "/python"

# 021554.python.redirector_with_filter.line53.comment The key feature of this redirector over the simple redirector is that it
# 021555.python.redirector_with_filter.line54.comment can choose to ignore certain responses by having the filter not rewrite them
# 021556.python.redirector_with_filter.line55.comment to our virtual dir. For this sample, we just exclude the IIS help directory.


# 021557.python.redirector_with_filter.line58.comment The ISAPI extension - handles requests in our virtual dir, and sends the
# 021558.python.redirector_with_filter.line59.comment response to the client.
class Extension(threaded_extension.ThreadPoolExtension):
    "Python sample Extension"

    def Dispatch(self, ecb):
        # 021559.python.redirector_with_filter.line64.comment Note that our ThreadPoolExtension base class will catch exceptions
        # 021560.python.redirector_with_filter.line65.comment in our Dispatch method, and write the traceback to the client.
        # 021561.python.redirector_with_filter.line66.comment That is perfect for this sample, so we don't catch our own.
        # 021562.python.redirector_with_filter.line67.comment print(f'IIS dispatching "{ecb.GetServerVariable("URL")}"')
        url = ecb.GetServerVariable("URL")
        if url.startswith(virtualdir):
            new_url = proxy + url[len(virtualdir) :]
            print("Opening", new_url)
            fp = urllib.request.urlopen(new_url)
            headers = fp.info()
            ecb.SendResponseHeaders("200 OK", str(headers) + "\r\n", False)
            ecb.WriteClient(fp.read())
            ecb.DoneWithSession()
            print(f"Returned data from '{new_url}'!")
        else:
            # 021563.python.redirector_with_filter.line79.comment this should never happen - we should only see requests that
            # 021564.python.redirector_with_filter.line80.comment start with our virtual directory name.
            print(f"Not proxying '{url}'")


# 021565.python.redirector_with_filter.line84.comment The ISAPI filter.
class Filter(SimpleFilter):
    "Sample Python Redirector"

    filter_flags = isapicon.SF_NOTIFY_PREPROC_HEADERS | isapicon.SF_NOTIFY_ORDER_DEFAULT

    def HttpFilterProc(self, fc):
        # 021566.python.redirector_with_filter.line91.comment print("Filter Dispatch")
        nt = fc.NotificationType
        if nt != isapicon.SF_NOTIFY_PREPROC_HEADERS:
            return isapicon.SF_STATUS_REQ_NEXT_NOTIFICATION

        pp = fc.GetData()
        url = pp.GetHeader("url")
        # 021567.python.redirector_with_filter.line98.comment print(f"URL is '{url}'")
        prefix = virtualdir
        if not url.startswith(prefix):
            new_url = prefix + url
            print(f"New proxied URL is '{new_url}'")
            pp.SetHeader("url", new_url)
            # 021568.python.redirector_with_filter.line104.comment For the sake of demonstration, show how the FilterContext
            # 021569.python.redirector_with_filter.line105.comment attribute is used.  It always starts out life as None, and
            # 021570.python.redirector_with_filter.line106.comment any assignments made are automatically decref'd by the
            # 021571.python.redirector_with_filter.line107.comment framework during a SF_NOTIFY_END_OF_NET_SESSION notification.
            if fc.FilterContext is None:
                fc.FilterContext = 0
            fc.FilterContext += 1
            print("This is request number %d on this connection" % fc.FilterContext)
            return isapicon.SF_STATUS_REQ_HANDLED_NOTIFICATION
        else:
            print(f"Filter ignoring URL '{url}'")

            # 021572.python.redirector_with_filter.line116.comment Some older code that handled SF_NOTIFY_URL_MAP.
            # 021573.python.redirector_with_filter.line117.comment print("Have URL_MAP notify")
            # 021574.python.redirector_with_filter.line118.comment urlmap = fc.GetData()
            # 021575.python.redirector_with_filter.line119.comment print("URI is", urlmap.URL)
            # 021576.python.redirector_with_filter.line120.comment print("Path is", urlmap.PhysicalPath)
            # 021577.python.redirector_with_filter.line121.comment if urlmap.URL.startswith("/UC/"):
            # 021578.python.redirector_with_filter.line122.comment # Find the /UC/ in the physical path, and nuke it (except
            # 021579.python.redirector_with_filter.line123.comment # as the path is physical, it is \)
            # 021580.python.redirector_with_filter.line124.comment p = urlmap.PhysicalPath
            # 021581.python.redirector_with_filter.line125.comment pos = p.index("\\UC\\")
            # 021582.python.redirector_with_filter.line126.comment p = p[:pos] + p[pos+3:]
            # 021583.python.redirector_with_filter.line127.comment p = r"E:\src\pyisapi\webroot\PyTest\formTest.htm"
            # 021584.python.redirector_with_filter.line128.comment print("New path is", p)
            # 021585.python.redirector_with_filter.line129.comment urlmap.PhysicalPath = p


# 021586.python.redirector_with_filter.line132.comment The entry points for the ISAPI extension.
def __FilterFactory__():
    return Filter()


def __ExtensionFactory__():
    return Extension()


if __name__ == "__main__":
    # 021587.python.redirector_with_filter.line142.comment If run from the command-line, install ourselves.
    from isapi.install import *

    params = ISAPIParameters()
    # 021588.python.redirector_with_filter.line146.comment Setup all filters - these are global to the site.
    params.Filters = [
        FilterParameters(Name="PythonRedirector", Description=Filter.__doc__),
    ]
    # 021589.python.redirector_with_filter.line150.comment Setup the virtual directories - this is a list of directories our
    # 021590.python.redirector_with_filter.line151.comment extension uses - in this case only 1.
    # 021591.python.redirector_with_filter.line152.comment Each extension has a "script map" - this is the mapping of ISAPI
    # 021592.python.redirector_with_filter.line153.comment extensions.
    sm = [ScriptMapParams(Extension="*", Flags=0)]
    vd = VirtualDirParameters(
        Name=virtualdir[1:],
        Description=Extension.__doc__,
        ScriptMaps=sm,
        ScriptMapUpdate="replace",
    )
    params.VirtualDirs = [vd]
    HandleCommandLine(params)
