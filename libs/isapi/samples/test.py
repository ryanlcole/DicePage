# 021593.python.test.line1.comment This extension is used mainly for testing purposes - it is not
# 021594.python.test.line2.comment designed to be a simple sample, but instead is a hotch-potch of things
# 021595.python.test.line3.comment that attempts to exercise the framework.

import os
import stat
import sys

from isapi import isapicon
from isapi.simple import SimpleExtension

if hasattr(sys, "isapidllhandle"):
    import win32traceutil

# 021596.python.test.line15.comment We use the same reload support as 'advanced.py' demonstrates.
import threading

import win32con
import win32event
import win32file
import winerror

from isapi import InternalReloadException


# 021597.python.test.line26.comment A watcher thread that checks for __file__ changing.
# 021598.python.test.line27.comment When it detects it, it simply sets "change_detected" to true.
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
                # 021600.python.test.line48.comment handle closed - thread should terminate.
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


def TransmitFileCallback(ecb, hFile, cbIO, errCode):
    print("Transmit complete!")
    ecb.close()


# 021601.python.test.line67.comment The ISAPI extension - handles requests in our virtual dir, and sends the
# 021602.python.test.line68.comment response to the client.
class Extension(SimpleExtension):
    "Python test Extension"

    def __init__(self):
        self.reload_watcher = ReloadWatcherThread()
        self.reload_watcher.start()

    def HttpExtensionProc(self, ecb):
        # 021603.python.test.line77.comment NOTE: If you use a ThreadPoolExtension, you must still perform
        # 021604.python.test.line78.comment this check in HttpExtensionProc - raising the exception from
        # 021605.python.test.line79.comment The "Dispatch" method will just cause the exception to be
        # 021606.python.test.line80.comment rendered to the browser.
        if self.reload_watcher.change_detected:
            print("Doing reload")
            raise InternalReloadException

        if ecb.GetServerVariable("UNICODE_URL").endswith("test.py"):
            file_flags = (
                win32con.FILE_FLAG_SEQUENTIAL_SCAN | win32con.FILE_FLAG_OVERLAPPED
            )
            hfile = win32file.CreateFile(
                __file__,
                win32con.GENERIC_READ,
                0,
                None,
                win32con.OPEN_EXISTING,
                file_flags,
                None,
            )
            flags = (
                isapicon.HSE_IO_ASYNC
                | isapicon.HSE_IO_DISCONNECT_AFTER_SEND
                | isapicon.HSE_IO_SEND_HEADERS
            )
            # 021607.python.test.line103.comment We pass hFile to the callback simply as a way of keeping it alive
            # 021608.python.test.line104.comment for the duration of the transmission
            try:
                ecb.TransmitFile(
                    TransmitFileCallback,
                    hfile,
                    int(hfile),
                    "200 OK",
                    0,
                    0,
                    None,
                    None,
                    flags,
                )
            except:
                # 021609.python.test.line118.comment Errors keep this source file open!
                hfile.Close()
                raise
        else:
            # 021610.python.test.line122.comment default response
            ecb.SendResponseHeaders("200 OK", "Content-Type: text/html\r\n\r\n", 0)
            print("<HTML><BODY>", file=ecb)
            print("The root of this site is at", ecb.MapURLToPath("/"), file=ecb)
            print("</BODY></HTML>", file=ecb)
            ecb.close()
        return isapicon.HSE_STATUS_SUCCESS

    def TerminateExtension(self, status):
        self.reload_watcher.stop()


# 021611.python.test.line134.comment The entry points for the ISAPI extension.
def __ExtensionFactory__():
    return Extension()


# 021612.python.test.line139.comment Our special command line customization.
# 021613.python.test.line140.comment Pre-install hook for our virtual directory.
def PreInstallDirectory(params, options):
    # 021614.python.test.line142.comment If the user used our special '--description' option,
    # 021615.python.test.line143.comment then we override our default.
    if options.description:
        params.Description = options.description


# 021616.python.test.line148.comment Post install hook for our entire script
def PostInstall(params, options):
    print()
    print("The sample has been installed.")
    print("Point your browser to /PyISAPITest")


# 021617.python.test.line155.comment Handler for our custom 'status' argument.
def status_handler(options, log, arg):
    "Query the status of something"
    print("Everything seems to be fine!")


custom_arg_handlers = {"status": status_handler}

if __name__ == "__main__":
    # 021618.python.test.line164.comment If run from the command-line, install ourselves.
    from isapi.install import *

    params = ISAPIParameters(PostInstall=PostInstall)
    # 021619.python.test.line168.comment Setup the virtual directories - this is a list of directories our
    # 021620.python.test.line169.comment extension uses - in this case only 1.
    # 021621.python.test.line170.comment Each extension has a "script map" - this is the mapping of ISAPI
    # 021622.python.test.line171.comment extensions.
    sm = [ScriptMapParams(Extension="*", Flags=0)]
    vd = VirtualDirParameters(
        Name="PyISAPITest",
        Description=Extension.__doc__,
        ScriptMaps=sm,
        ScriptMapUpdate="replace",
        # 021623.python.test.line178.comment specify the pre-install hook.
        PreInstall=PreInstallDirectory,
    )
    params.VirtualDirs = [vd]
    # 021624.python.test.line182.comment Setup our custom option parser.
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
