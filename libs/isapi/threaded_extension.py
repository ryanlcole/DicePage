"""An ISAPI extension base class implemented using a thread-pool."""

# 021654.python.threaded_extension.line3.comment $Id$

import sys
import threading
import time
import traceback

from pywintypes import OVERLAPPED
from win32event import INFINITE
from win32file import (
    CloseHandle,
    CreateIoCompletionPort,
    GetQueuedCompletionStatus,
    PostQueuedCompletionStatus,
)
from win32security import SetThreadToken

import isapi.simple
from isapi import ExtensionError, isapicon

ISAPI_REQUEST = 1
ISAPI_SHUTDOWN = 2


class WorkerThread(threading.Thread):
    def __init__(self, extension, io_req_port):
        self.running = False
        self.io_req_port = io_req_port
        self.extension = extension
        threading.Thread.__init__(
            self,
            # 021655.python.threaded_extension.line34.comment We wait 15 seconds for a thread to terminate, but if it fails to,
            # 021656.python.threaded_extension.line35.comment we don't want the process to hang at exit waiting for it...
            daemon=True,
        )

    def run(self):
        self.running = True
        while self.running:
            errCode, bytes, key, overlapped = GetQueuedCompletionStatus(
                self.io_req_port, INFINITE
            )
            if key == ISAPI_SHUTDOWN and overlapped is None:
                break

            # 021657.python.threaded_extension.line48.comment Let the parent extension handle the command.
            dispatcher = self.extension.dispatch_map.get(key)
            if dispatcher is None:
                raise RuntimeError(f"Bad request '{key}'")

            dispatcher(errCode, bytes, key, overlapped)

    def call_handler(self, cblock):
        self.extension.Dispatch(cblock)


# 021658.python.threaded_extension.line59.comment A generic thread-pool based extension, using IO Completion Ports.
# 021659.python.threaded_extension.line60.comment Sub-classes can override one method to implement a simple extension, or
# 021660.python.threaded_extension.line61.comment may leverage the CompletionPort to queue their own requests, and implement a
# 021661.python.threaded_extension.line62.comment fully asynch extension.
class ThreadPoolExtension(isapi.simple.SimpleExtension):
    "Base class for an ISAPI extension based around a thread-pool"

    max_workers = 20
    worker_shutdown_wait = 15000  # 15 seconds for workers to quit...

    def __init__(self):
        self.workers = []
        # 021663.python.threaded_extension.line71.comment extensible dispatch map, for sub-classes that need to post their
        # 021664.python.threaded_extension.line72.comment own requests to the completion port.
        # 021665.python.threaded_extension.line73.comment Each of these functions is called with the result of
        # 021666.python.threaded_extension.line74.comment GetQueuedCompletionStatus for our port.
        self.dispatch_map = {
            ISAPI_REQUEST: self.DispatchConnection,
        }

    def GetExtensionVersion(self, vi):
        isapi.simple.SimpleExtension.GetExtensionVersion(self, vi)
        # 021667.python.threaded_extension.line81.comment As per Q192800, the CompletionPort should be created with the number
        # 021668.python.threaded_extension.line82.comment of processors, even if the number of worker threads is much larger.
        # 021669.python.threaded_extension.line83.comment Passing 0 means the system picks the number.
        self.io_req_port = CreateIoCompletionPort(-1, None, 0, 0)
        # 021670.python.threaded_extension.line85.comment start up the workers
        self.workers = []
        for i in range(self.max_workers):
            worker = WorkerThread(self, self.io_req_port)
            worker.start()
            self.workers.append(worker)

    def HttpExtensionProc(self, control_block):
        overlapped = OVERLAPPED()
        overlapped.object = control_block
        PostQueuedCompletionStatus(self.io_req_port, 0, ISAPI_REQUEST, overlapped)
        return isapicon.HSE_STATUS_PENDING

    def TerminateExtension(self, status):
        for worker in self.workers:
            worker.running = False
        for worker in self.workers:
            PostQueuedCompletionStatus(self.io_req_port, 0, ISAPI_SHUTDOWN, None)
        # 021671.python.threaded_extension.line103.comment wait for them to terminate - pity we aren't using 'native' threads
        # 021672.python.threaded_extension.line104.comment as then we could do a smart wait - but now we need to poll....
        end_time = time.time() + self.worker_shutdown_wait / 1000
        alive = self.workers
        while alive:
            if time.time() > end_time:
                # 021673.python.threaded_extension.line109.comment xxx - might be nice to log something here.
                break
            time.sleep(0.2)
            alive = [w for w in alive if w.is_alive()]
        self.dispatch_map = {}  # break circles
        CloseHandle(self.io_req_port)

    # 021675.python.threaded_extension.line116.comment This is the one operation the base class supports - a simple
    # 021676.python.threaded_extension.line117.comment Connection request.  We setup the thread-token, and dispatch to the
    # 021677.python.threaded_extension.line118.comment sub-class's 'Dispatch' method.
    def DispatchConnection(self, errCode, bytes, key, overlapped):
        control_block = overlapped.object
        # 021678.python.threaded_extension.line121.comment setup the correct user for this request
        hRequestToken = control_block.GetImpersonationToken()
        SetThreadToken(None, hRequestToken)
        try:
            try:
                self.Dispatch(control_block)
            except:
                self.HandleDispatchError(control_block)
        finally:
            # 021679.python.threaded_extension.line130.comment reset the security context
            SetThreadToken(None, None)

    def Dispatch(self, ecb):
        """Overridden by the sub-class to handle connection requests.

        This class creates a thread-pool using a Windows completion port,
        and dispatches requests via this port.  Sub-classes can generally
        implement each connection request using blocking reads and writes, and
        the thread-pool will still provide decent response to the end user.

        The sub-class can set a max_workers attribute (default is 20).  Note
        that this generally does *not* mean 20 threads will all be concurrently
        running, via the magic of Windows completion ports.

        There is no default implementation - sub-classes must implement this.
        """
        raise NotImplementedError("sub-classes should override Dispatch")

    def HandleDispatchError(self, ecb):
        """Handles errors in the Dispatch method.

        When a Dispatch method call fails, this method is called to handle
        the exception.  The default implementation formats the traceback
        in the browser.
        """
        ecb.HttpStatusCode = isapicon.HSE_STATUS_ERROR
        # 021680.python.threaded_extension.line157.comment control_block.LogData = "we failed!"
        exc_typ, exc_val, exc_tb = sys.exc_info()
        limit = None
        try:
            try:
                import html

                ecb.SendResponseHeaders(
                    "200 OK", "Content-type: text/html\r\n\r\n", False
                )
                print(file=ecb)
                print("<H3>Traceback (most recent call last):</H3>", file=ecb)
                list = traceback.format_tb(
                    exc_tb, limit
                ) + traceback.format_exception_only(exc_typ, exc_val)
                bold = list.pop()
                print(
                    "<PRE>{}<B>{}</B></PRE>".format(
                        html.escape("".join(list)),
                        html.escape(bold),
                    ),
                    file=ecb,
                )
            except ExtensionError:
                # 021681.python.threaded_extension.line181.comment The client disconnected without reading the error body -
                # 021682.python.threaded_extension.line182.comment it's probably not a real browser at the other end, ignore it.
                pass
            except:
                print("FAILED to render the error message!")
                traceback.print_exc()
                print("ORIGINAL extension error:")
                traceback.print_exception(exc_typ, exc_val, exc_tb)
        finally:
            # 021683.python.threaded_extension.line190.comment holding tracebacks in a local of a frame that may itself be
            # 021684.python.threaded_extension.line191.comment part of a traceback used to be evil and cause leaks!
            exc_tb = None
            ecb.DoneWithSession()
