# 021391.python.advanced.line1.comment This extension demonstrates some advanced features of the Python ISAPI
# 021392.python.advanced.line2.comment framework.
# 021393.python.advanced.line3.comment We demonstrate:
# 021394.python.advanced.line4.comment * Reloading your Python module without shutting down IIS (eg, when your
# 021395.python.advanced.line5.comment .py implementation file changes.)
# 021396.python.advanced.line6.comment * Custom command-line handling - both additional options and commands.
# 021397.python.advanced.line7.comment * Using a query string - any part of the URL after a '?' is assumed to
# 021398.python.advanced.line8.comment be "variable names" separated by '&' - we will print the values of
# 021399.python.advanced.line9.comment these server variables.
# 021400.python.advanced.line10.comment * If the tail portion of the URL is "ReportUnhealthy", IIS will be
# 021401.python.advanced.line11.comment notified we are unhealthy via a HSE_REQ_REPORT_UNHEALTHY request.
# 021402.python.advanced.line12.comment Whether this is acted upon depends on if the IIS health-checking
# 021403.python.advanced.line13.comment tools are installed, but you should always see the reason written
# 021404.python.advanced.line14.comment to the Windows event log - see the IIS documentation for more.

import os
import stat
import sys

from isapi import isapicon
from isapi.simple import SimpleExtension

if hasattr(sys, "isapidllhandle"):
    import win32traceutil

# 021405.python.advanced.line26.comment Notes on reloading
# 021406.python.advanced.line27.comment If your HttpFilterProc or HttpExtensionProc functions raises
# 021407.python.advanced.line28.comment 'isapi.InternalReloadException', the framework will not treat it
# 021408.python.advanced.line29.comment as an error but instead will terminate your extension, reload your
# 021409.python.advanced.line30.comment extension module, re-initialize the instance, and re-issue the request.
# 021410.python.advanced.line31.comment The Initialize functions are called with None as their param.  The
# 021411.python.advanced.line32.comment return code from the terminate function is ignored.
# 021412.python.advanced.line33.comment
# 021413.python.advanced.line34.comment This is all the framework does to help you.  It is up to your code
# 021414.python.advanced.line35.comment when you raise this exception.  This sample uses a Win32 "find
# 021415.python.advanced.line36.comment notification".  Whenever windows tells us one of the files in the
# 021416.python.advanced.line37.comment directory has changed, we check if the time of our source-file has
# 021417.python.advanced.line38.comment changed, and set a flag.  Next imcoming request, we check the flag and
# 021418.python.advanced.line39.comment raise the special exception if set.
# 021419.python.advanced.line40.comment
# 021420.python.advanced.line41.comment The end result is that the module is automatically reloaded whenever
# 021421.python.advanced.line42.comment the source-file changes - you need take no further action to see your
# 021422.python.advanced.line43.comment changes reflected in the running server.

# 021423.python.advanced.line45.comment The framework only reloads your module - if you have libraries you
# 021424.python.advanced.line46.comment depend on and also want reloaded, you must arrange for this yourself.
# 021425.python.advanced.line47.comment One way of doing this would be to special case the import of these
# 021426.python.advanced.line48.comment modules.  Eg:
# 021427.python.advanced.line49.comment --
# 021428.python.advanced.line50.comment try:
# 021429.python.advanced.line51.comment my_module = reload(my_module) # module already imported - reload it
# 021430.python.advanced.line52.comment except NameError:
# 021431.python.advanced.line53.comment import my_module # first time around - import it.
# 021432.python.advanced.line54.comment --
# 021433.python.advanced.line55.comment When your module is imported for the first time, the NameError will
# 021434.python.advanced.line56.comment be raised, and the module imported.  When the ISAPI framework reloads
# 021435.python.advanced.line57.comment your module, the existing module will avoid the NameError, and allow
# 021436.python.advanced.line58.comment you to reload that module.

import threading

import win32con
import win32event
import win32file
import winerror

from isapi import InternalReloadException

try:
    reload_counter += 1  # type: ignore[used-before-def]
except NameError:
    reload_counter = 0


# 021438.python.advanced.line75.comment A watcher thread that checks for __file__ changing.
# 021439.python.advanced.line76.comment When it detects it, it simply sets "change_detected" to true.
class ReloadWatcherThread(threading.Thread):
    def __init__(self):
        self.change_detected = False
        self.filename = __file__
        if self.filename.endswith("c") or self.filename.endswith("o"):
            self.filename = self.filename[:-1]
        self.handle = win32file.FindFirstChangeNotification(
            os.path.dirname(self.filename),
            False,  # watch tree?
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
        )
        threading.Thread.__init__(self)

    def run(self):
        last_time = os.stat(self.filename)[stat.ST_MTIME]
        while 1:
            try:
                rc = win32event.WaitForSingleObject(self.handle, win32event.INFINITE)
                win32file.FindNextChangeNotification(self.handle)
            except win32event.error as details:
                # 021441.python.advanced.line97.comment handle closed - thread should terminate.
                if details.winerror != winerror.ERROR_INVALID_HANDLE:
                    raise
                break
            this_time = os.stat(self.filename)[stat.ST_MTIME]
            if this_time != last_time:
                print("Detected file change - flagging for reload.")
                self.change_detected = True
                last_time = this_time

    def stop(self):
        win32file.FindCloseChangeNotification(self.handle)


# 021442.python.advanced.line111.comment The ISAPI extension - handles requests in our virtual dir, and sends the
# 021443.python.advanced.line112.comment response to the client.
class Extension(SimpleExtension):
    "Python advanced sample Extension"

    def __init__(self):
        self.reload_watcher = ReloadWatcherThread()
        self.reload_watcher.start()

    def HttpExtensionProc(self, ecb):
        # 021444.python.advanced.line121.comment NOTE: If you use a ThreadPoolExtension, you must still perform
        # 021445.python.advanced.line122.comment this check in HttpExtensionProc - raising the exception from
        # 021446.python.advanced.line123.comment The "Dispatch" method will just cause the exception to be
        # 021447.python.advanced.line124.comment rendered to the browser.
        if self.reload_watcher.change_detected:
            print("Doing reload")
            raise InternalReloadException

        url = ecb.GetServerVariable("UNICODE_URL")
        if url.endswith("ReportUnhealthy"):
            ecb.ReportUnhealthy("I'm a little sick")

        ecb.SendResponseHeaders("200 OK", "Content-Type: text/html\r\n\r\n", 0)
        print("<HTML><BODY>", file=ecb)

        qs = ecb.GetServerVariable("QUERY_STRING")
        if qs:
            queries = qs.split("&")
            print("<PRE>", file=ecb)
            for q in queries:
                val = ecb.GetServerVariable(q, "&lt;no such variable&gt;")
                print(f"{q}={val!r}", file=ecb)
            print("</PRE><P/>", file=ecb)

        print("This module has been imported", file=ecb)
        print("%d times" % (reload_counter,), file=ecb)
        print("</BODY></HTML>", file=ecb)
        ecb.close()
        return isapicon.HSE_STATUS_SUCCESS

    def TerminateExtension(self, status):
        self.reload_watcher.stop()


# 021448.python.advanced.line155.comment The entry points for the ISAPI extension.
def __ExtensionFactory__():
    return Extension()


# 021449.python.advanced.line160.comment Our special command line customization.
# 021450.python.advanced.line161.comment Pre-install hook for our virtual directory.
def PreInstallDirectory(params, options):
    # 021451.python.advanced.line163.comment If the user used our special '--description' option,
    # 021452.python.advanced.line164.comment then we override our default.
    if options.description:
        params.Description = options.description


# 021453.python.advanced.line169.comment Post install hook for our entire script
def PostInstall(params, options):
    print()
    print("The sample has been installed.")
    print("Point your browser to /AdvancedPythonSample")
    print("If you modify the source file and reload the page,")
    print("you should see the reload counter increment")


# 021454.python.advanced.line178.comment Handler for our custom 'status' argument.
def status_handler(options, log, arg):
    "Query the status of something"
    print("Everything seems to be fine!")


custom_arg_handlers = {"status": status_handler}

if __name__ == "__main__":
    # 021455.python.advanced.line187.comment If run from the command-line, install ourselves.
    from isapi.install import *

    params = ISAPIParameters(PostInstall=PostInstall)
    # 021456.python.advanced.line191.comment Setup the virtual directories - this is a list of directories our
    # 021457.python.advanced.line192.comment extension uses - in this case only 1.
    # 021458.python.advanced.line193.comment Each extension has a "script map" - this is the mapping of ISAPI
    # 021459.python.advanced.line194.comment extensions.
    sm = [ScriptMapParams(Extension="*", Flags=0)]
    vd = VirtualDirParameters(
        Name="AdvancedPythonSample",
        Description=Extension.__doc__,
        ScriptMaps=sm,
        ScriptMapUpdate="replace",
        # 021460.python.advanced.line201.comment specify the pre-install hook.
        PreInstall=PreInstallDirectory,
    )
    params.VirtualDirs = [vd]
    # 021461.python.advanced.line205.comment Setup our custom option parser.
    from optparse import OptionParser

    parser = OptionParser("")  # blank usage, so isapi sets it.
    parser.add_option(
        "",
        "--description",
        action="store",
        help="custom description to use for the virtual directory",
    )

    HandleCommandLine(
        params, opt_parser=parser, custom_arg_handlers=custom_arg_handlers
    )
