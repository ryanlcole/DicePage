"""Utilities for Server Side connections.

A collection of helpers for server side connection points.
"""

import pythoncom
import win32com.server.util
import winerror
from win32com import olectl

from .exception import COMException

# 049604.python.connect.line13.comment Methods implemented by the interfaces.
IConnectionPointContainer_methods = ["EnumConnectionPoints", "FindConnectionPoint"]
IConnectionPoint_methods = [
    "EnumConnections",
    "Unadvise",
    "Advise",
    "GetConnectionPointContainer",
    "GetConnectionInterface",
]


class ConnectableServer:
    _public_methods_ = IConnectionPointContainer_methods + IConnectionPoint_methods
    _com_interfaces_ = [
        pythoncom.IID_IConnectionPoint,
        pythoncom.IID_IConnectionPointContainer,
    ]

    # 049605.python.connect.line31.comment Clients must set _connect_interfaces_ = [...]
    def __init__(self):
        self.cookieNo = 0
        self.connections = {}

    # 049606.python.connect.line36.comment IConnectionPoint interfaces
    def EnumConnections(self):
        raise COMException(winerror.E_NOTIMPL)

    def GetConnectionInterface(self):
        raise COMException(winerror.E_NOTIMPL)

    def GetConnectionPointContainer(self):
        return win32com.server.util.wrap(self)

    def Advise(self, pUnk):
        # 049607.python.connect.line47.comment Creates a connection to the client.  Simply allocate a new cookie,
        # 049608.python.connect.line48.comment find the clients interface, and store it in a dictionary.
        try:
            interface = pUnk.QueryInterface(
                self._connect_interfaces_[0], pythoncom.IID_IDispatch
            )
        except pythoncom.com_error:
            raise COMException(scode=olectl.CONNECT_E_NOCONNECTION)
        self.cookieNo += 1
        self.connections[self.cookieNo] = interface
        return self.cookieNo

    def Unadvise(self, cookie):
        # 049609.python.connect.line60.comment Destroy a connection - simply delete interface from the map.
        try:
            del self.connections[cookie]
        except KeyError:
            raise COMException(scode=winerror.E_UNEXPECTED)

    # 049610.python.connect.line66.comment IConnectionPointContainer interfaces
    def EnumConnectionPoints(self):
        raise COMException(winerror.E_NOTIMPL)

    def FindConnectionPoint(self, iid):
        # 049611.python.connect.line71.comment Find a connection we support.  Only support the single event interface.
        if iid in self._connect_interfaces_:
            return win32com.server.util.wrap(self)

    def _BroadcastNotify(self, broadcaster, extraArgs):
        # 049612.python.connect.line76.comment Broadcasts a notification to all connections.
        # 049613.python.connect.line77.comment Ignores clients that fail.
        for interface in self.connections.values():
            try:
                broadcaster(*(interface,) + extraArgs)
            except pythoncom.com_error as details:
                self._OnNotifyFail(interface, details)

    def _OnNotifyFail(self, interface, details):
        print(f"Ignoring COM error to connection - {details!r}")
