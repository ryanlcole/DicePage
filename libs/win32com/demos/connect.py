# 049183.python.connect.line1.comment Implements _both_ a connectable client, and a connectable server.
# 049184.python.connect.line2.comment
# 049185.python.connect.line3.comment Note that we cheat just a little - the Server in this demo is not created
# 049186.python.connect.line4.comment via Normal COM - this means we can avoid registering the server.
# 049187.python.connect.line5.comment However, the server _is_ accessed as a COM object - just the creation
# 049188.python.connect.line6.comment is cheated on - so this is still working as a fully-fledged server.

import pythoncom
import pywintypes
import win32com.server.connect
import win32com.server.util

# 049189.python.connect.line13.comment This is the IID of the Events interface both Client and Server support.
IID_IConnectDemoEvents = pywintypes.IID("{A4988850-49C3-11d0-AE5D-52342E000000}")

# 049190.python.connect.line16.comment The server which implements
# 049191.python.connect.line17.comment Create a connectable class, that has a single public method
# 049192.python.connect.line18.comment 'DoIt', which echos to a single sink 'DoneIt'


class ConnectableServer(win32com.server.connect.ConnectableServer):
    _public_methods_ = [
        "DoIt"
    ] + win32com.server.connect.ConnectableServer._public_methods_
    _connect_interfaces_ = [IID_IConnectDemoEvents]

    # 049193.python.connect.line27.comment The single public method that the client can call on us
    # 049194.python.connect.line28.comment (ie, as a normal COM server, this exposes just this single method.
    def DoIt(self, arg):
        # 049195.python.connect.line30.comment Simply broadcast a notification.
        self._BroadcastNotify(self.NotifyDoneIt, (arg,))

    def NotifyDoneIt(self, interface, arg):
        interface.Invoke(1000, 0, pythoncom.DISPATCH_METHOD, 1, arg)


# 049196.python.connect.line37.comment Here is the client side of the connection world.
# 049197.python.connect.line38.comment Define a COM object which implements the methods defined by the
# 049198.python.connect.line39.comment IConnectDemoEvents interface.
class ConnectableClient:
    # 049199.python.connect.line41.comment This is another cheat - I _know_ the server defines the "DoneIt" event
    # 049200.python.connect.line42.comment as DISPID==1000 - I also know from the implementation details of COM
    # 049201.python.connect.line43.comment that the first method in _public_methods_ gets 1000.
    # 049202.python.connect.line44.comment Normally some explicit DISPID->Method mapping is required.
    _public_methods_ = ["OnDoneIt"]

    def __init__(self):
        self.last_event_arg = None

    # 049203.python.connect.line50.comment A client must implement QI, and respond to a query for the Event interface.
    # 049204.python.connect.line51.comment In addition, it must provide a COM object (which server.util.wrap) does.
    def _query_interface_(self, iid):
        # 049205.python.connect.line53.comment Note that this seems like a necessary hack.  I am responding to IID_IConnectDemoEvents
        # 049206.python.connect.line54.comment but only creating an IDispatch gateway object.
        if iid == IID_IConnectDemoEvents:
            return win32com.server.util.wrap(self)

    # 049207.python.connect.line58.comment And here is our event method which gets called.
    def OnDoneIt(self, arg):
        self.last_event_arg = arg


def CheckEvent(server, client, val, verbose):
    client.last_event_arg = None
    server.DoIt(val)
    if client.last_event_arg != val:
        raise RuntimeError(f"Sent {val!r}, but got back {client.last_event_arg!r}")
    if verbose:
        print("Sent and received %r" % val)


# 049208.python.connect.line72.comment A simple test script for all this.
# 049209.python.connect.line73.comment In the real world, it is likely that the code controlling the server
# 049210.python.connect.line74.comment will be in the same class as that getting the notifications.
def test(verbose=0):
    import win32com.client.connect
    import win32com.client.dynamic
    import win32com.server.policy

    server = win32com.client.dynamic.Dispatch(
        win32com.server.util.wrap(ConnectableServer())
    )
    connection = win32com.client.connect.SimpleConnection()
    client = ConnectableClient()
    connection.Connect(server, client, IID_IConnectDemoEvents)
    CheckEvent(server, client, "Hello", verbose)
    CheckEvent(server, client, b"Here is a null>\x00<", verbose)
    CheckEvent(server, client, "Here is a null>\x00<", verbose)
    val = "test-\xe0\xf2"  # 2 extended characters.
    CheckEvent(server, client, val, verbose)
    if verbose:
        print("Everything seemed to work!")
    # 049212.python.connect.line93.comment Aggressive memory leak checking (ie, do nothing!) :-)  All should cleanup OK???


if __name__ == "__main__":
    test(1)
