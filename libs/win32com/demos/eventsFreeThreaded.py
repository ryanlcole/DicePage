# 049248.python.eventsFreeThreaded.line1.comment A sample originally provided by Richard Bell, and modified by Mark Hammond.

# 049249.python.eventsFreeThreaded.line3.comment This sample demonstrates how to use COM events in a free-threaded world.
# 049250.python.eventsFreeThreaded.line4.comment In this world, there is no need to marshall calls across threads, so
# 049251.python.eventsFreeThreaded.line5.comment no message loops are needed at all.  This means regular cross-thread
# 049252.python.eventsFreeThreaded.line6.comment sychronization can be used.  In this sample we just wait on win32 event
# 049253.python.eventsFreeThreaded.line7.comment objects.

# 049254.python.eventsFreeThreaded.line9.comment See also ieEventsApartmentThreaded.py for how to do this in an
# 049255.python.eventsFreeThreaded.line10.comment aparment-threaded world, where thread-marshalling complicates things.

# 049256.python.eventsFreeThreaded.line12.comment NOTE: This example uses Internet Explorer, but it should not be considerd
# 049257.python.eventsFreeThreaded.line13.comment a "best-practices" for writing against IE events, but for working with
# 049258.python.eventsFreeThreaded.line14.comment events in general. For example:
# 049259.python.eventsFreeThreaded.line15.comment * The first OnDocumentComplete event is not a reliable indicator that the
# 049260.python.eventsFreeThreaded.line16.comment URL has completed loading
# 049261.python.eventsFreeThreaded.line17.comment * As we are demonstrating the most efficient way of handling events, when
# 049262.python.eventsFreeThreaded.line18.comment running this sample you will see an IE Windows briefly appear, but
# 049263.python.eventsFreeThreaded.line19.comment vanish without ever being repainted.

import sys

sys.coinit_flags = 0  # specify free threading


import pythoncom
import win32api
import win32com.client
import win32event


# 049265.python.eventsFreeThreaded.line32.comment The print statements indicate that COM has actually started another thread
# 049266.python.eventsFreeThreaded.line33.comment and will deliver the events to that thread (ie, the events do not actually
# 049267.python.eventsFreeThreaded.line34.comment fire on our main thread.
class ExplorerEvents:
    def __init__(self):
        # 049268.python.eventsFreeThreaded.line37.comment We reuse this event for all events.
        self.event = win32event.CreateEvent(None, 0, 0, None)

    def OnDocumentComplete(self, pDisp=pythoncom.Empty, URL=pythoncom.Empty):
        # 049269.python.eventsFreeThreaded.line41.comment
        # 049270.python.eventsFreeThreaded.line42.comment Caution:  Since the main thread and events thread(s) are different
        # 049271.python.eventsFreeThreaded.line43.comment it may be necessary to serialize access to shared data.  Because
        # 049272.python.eventsFreeThreaded.line44.comment this is a simple test case, that is not required here.  Your
        # 049273.python.eventsFreeThreaded.line45.comment situation may be different.   Caveat programmer.
        # 049274.python.eventsFreeThreaded.line46.comment
        thread = win32api.GetCurrentThreadId()
        print("OnDocumentComplete event processed on thread %d" % thread)
        # 049275.python.eventsFreeThreaded.line49.comment Set the event our main thread is waiting on.
        win32event.SetEvent(self.event)

    def OnQuit(self):
        thread = win32api.GetCurrentThreadId()
        print("OnQuit event processed on thread %d" % thread)
        win32event.SetEvent(self.event)


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

    # 049276.python.eventsFreeThreaded.line72.comment In this free-threaded example, we can simply wait until an event has
    # 049277.python.eventsFreeThreaded.line73.comment been set - we will give it 2 seconds before giving up.
    rc = win32event.WaitForSingleObject(iexplore.event, 2000)
    if rc != win32event.WAIT_OBJECT_0:
        print("Document load event FAILED to fire!!!")

    iexplore.Quit()
    # 049278.python.eventsFreeThreaded.line79.comment Now we can do the same thing to wait for exit!
    # 049279.python.eventsFreeThreaded.line80.comment Although Quit generates events, in this free-threaded world we
    # 049280.python.eventsFreeThreaded.line81.comment do *not* need to run any message pumps.

    rc = win32event.WaitForSingleObject(iexplore.event, 2000)
    if rc != win32event.WAIT_OBJECT_0:
        print("OnQuit event FAILED to fire!!!")

    iexplore = None
    print("Finished the IE event sample!")


if __name__ == "__main__":
    TestExplorerEvents()
