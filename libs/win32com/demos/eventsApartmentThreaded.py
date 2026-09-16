# 049216.python.eventsApartmentThreaded.line1.comment A sample originally provided by Richard Bell, and modified by Mark Hammond.

# 049217.python.eventsApartmentThreaded.line3.comment This sample demonstrates how to use COM events in an aparment-threaded
# 049218.python.eventsApartmentThreaded.line4.comment world.  In this world, COM itself ensures that all calls to and events
# 049219.python.eventsApartmentThreaded.line5.comment from an object happen on the same thread that created the object, even
# 049220.python.eventsApartmentThreaded.line6.comment if they originated from different threads.  For this cross-thread
# 049221.python.eventsApartmentThreaded.line7.comment marshalling to work, this main thread *must* run a "message-loop" (ie,
# 049222.python.eventsApartmentThreaded.line8.comment a loop fetching and dispatching Windows messages).  Without such message
# 049223.python.eventsApartmentThreaded.line9.comment processing, dead-locks can occur.

# 049224.python.eventsApartmentThreaded.line11.comment See also eventsFreeThreaded.py for how to do this in a free-threaded
# 049225.python.eventsApartmentThreaded.line12.comment world where these marshalling considerations do not exist.

# 049226.python.eventsApartmentThreaded.line14.comment NOTE: This example uses Internet Explorer, but it should not be considerd
# 049227.python.eventsApartmentThreaded.line15.comment a "best-practices" for writing against IE events, but for working with
# 049228.python.eventsApartmentThreaded.line16.comment events in general. For example:
# 049229.python.eventsApartmentThreaded.line17.comment * The first OnDocumentComplete event is not a reliable indicator that the
# 049230.python.eventsApartmentThreaded.line18.comment URL has completed loading
# 049231.python.eventsApartmentThreaded.line19.comment * As we are demonstrating the most efficient way of handling events, when
# 049232.python.eventsApartmentThreaded.line20.comment running this sample you will see an IE Windows briefly appear, but
# 049233.python.eventsApartmentThreaded.line21.comment vanish without ever being repainted.

import time

# 049234.python.eventsApartmentThreaded.line25.comment sys.coinit_flags not set, so pythoncom initializes apartment-threaded.
import pythoncom
import win32api
import win32com.client
import win32event


class ExplorerEvents:
    def __init__(self):
        self.event = win32event.CreateEvent(None, 0, 0, None)

    def OnDocumentComplete(self, pDisp=pythoncom.Empty, URL=pythoncom.Empty):
        thread = win32api.GetCurrentThreadId()
        print("OnDocumentComplete event processed on thread %d" % thread)
        # 049235.python.eventsApartmentThreaded.line39.comment Set the event our main thread is waiting on.
        win32event.SetEvent(self.event)

    def OnQuit(self):
        thread = win32api.GetCurrentThreadId()
        print("OnQuit event processed on thread %d" % thread)
        win32event.SetEvent(self.event)


def WaitWhileProcessingMessages(event, timeout=2):
    start = time.perf_counter()
    while True:
        # 049236.python.eventsApartmentThreaded.line51.comment Wake 4 times a second - we can't just specify the
        # 049237.python.eventsApartmentThreaded.line52.comment full timeout here, as then it would reset for every
        # 049238.python.eventsApartmentThreaded.line53.comment message we process.
        rc = win32event.MsgWaitForMultipleObjects(
            (event,), 0, 250, win32event.QS_ALLEVENTS
        )
        if rc == win32event.WAIT_OBJECT_0:
            # 049239.python.eventsApartmentThreaded.line58.comment event signalled - stop now!
            return True
        if (time.perf_counter() - start) > timeout:
            # 049240.python.eventsApartmentThreaded.line61.comment Timeout expired.
            return False
        # 049241.python.eventsApartmentThreaded.line63.comment must be a message.
        pythoncom.PumpWaitingMessages()


def TestExplorerEvents():
    iexplore = win32com.client.DispatchWithEvents(
        "InternetExplorer.Application", ExplorerEvents
    )

    thread = win32api.GetCurrentThreadId()
    print("TestExplorerEvents created IE object on thread %d" % thread)

    iexplore.Visible = 1
    try:
        iexplore.Navigate(win32api.GetFullPathName("..\\readme.html"))
    except pythoncom.com_error as details:
        print("Warning - could not open the test HTML file", details)

    # 049242.python.eventsApartmentThreaded.line81.comment Wait for the event to be signalled while pumping messages.
    if not WaitWhileProcessingMessages(iexplore.event):
        print("Document load event FAILED to fire!!!")

    iexplore.Quit()
    # 049243.python.eventsApartmentThreaded.line86.comment
    # 049244.python.eventsApartmentThreaded.line87.comment Give IE a chance to shutdown, else it can get upset on fast machines.
    # 049245.python.eventsApartmentThreaded.line88.comment Note, Quit generates events.  Although this test does NOT catch them
    # 049246.python.eventsApartmentThreaded.line89.comment it is NECESSARY to pump messages here instead of a sleep so that the Quit
    # 049247.python.eventsApartmentThreaded.line90.comment happens properly!
    if not WaitWhileProcessingMessages(iexplore.event):
        print("OnQuit event FAILED to fire!!!")

    iexplore = None


if __name__ == "__main__":
    TestExplorerEvents()
