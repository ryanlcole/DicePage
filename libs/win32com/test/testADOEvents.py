import os
import time

import pythoncom
from win32com.client import DispatchWithEvents, constants

finished = 0  # Flag for the wait loop from (3) to test


class ADOEvents:  # event handler class
    def OnWillConnect(self, str, user, pw, opt, sts, cn):
        # 049912.python.testADOEvents.line12.comment Must have this event, as if it is not handled, ADO assumes the
        # 049913.python.testADOEvents.line13.comment operation is cancelled, and raises an error (Operation cancelled
        # 049914.python.testADOEvents.line14.comment by the user)
        pass

    def OnConnectComplete(self, error, status, connection):
        # 049915.python.testADOEvents.line18.comment Assume no errors, until we have the basic stuff
        # 049916.python.testADOEvents.line19.comment working. Now, "connection" should be an open
        # 049917.python.testADOEvents.line20.comment connection to my data source
        # 049918.python.testADOEvents.line21.comment Do the "something" from (2). For now, just
        # 049919.python.testADOEvents.line22.comment print the connection data source
        print("connection is", connection)
        print("Connected to", connection.Properties("Data Source"))
        # 049920.python.testADOEvents.line25.comment OK, our work is done. Let the main loop know
        global finished
        finished = 1

    def OnCommitTransComplete(self, pError, adStatus, pConnection):
        pass

    def OnInfoMessage(self, pError, adStatus, pConnection):
        pass

    def OnDisconnect(self, adStatus, pConnection):
        pass

    def OnBeginTransComplete(self, TransactionLevel, pError, adStatus, pConnection):
        pass

    def OnRollbackTransComplete(self, pError, adStatus, pConnection):
        pass

    def OnExecuteComplete(
        self, RecordsAffected, pError, adStatus, pCommand, pRecordset, pConnection
    ):
        pass

    def OnWillExecute(
        self,
        Source,
        CursorType,
        LockType,
        Options,
        adStatus,
        pCommand,
        pRecordset,
        pConnection,
    ):
        pass


def TestConnection(dbname):
    # 049921.python.testADOEvents.line64.comment Create the ADO connection object, and link the event
    # 049922.python.testADOEvents.line65.comment handlers into it
    c = DispatchWithEvents("ADODB.Connection", ADOEvents)

    # 049923.python.testADOEvents.line68.comment Initiate the asynchronous open
    dsn = "Driver={Microsoft Access Driver (*.mdb)};Dbq=%s" % dbname
    user = "system"
    pw = "manager"
    c.Open(dsn, user, pw, constants.adAsyncConnect)

    # 049924.python.testADOEvents.line74.comment Sit in a loop, until our event handler (above) sets the
    # 049925.python.testADOEvents.line75.comment "finished" flag or we time out.
    end_time = time.clock() + 10
    while time.clock() < end_time:
        # 049926.python.testADOEvents.line78.comment Pump messages so that COM gets a look in
        pythoncom.PumpWaitingMessages()
    if not finished:
        print("XXX - Failed to connect!")


def Test():
    from . import testAccess

    try:
        testAccess.GenerateSupport()
    except pythoncom.com_error:
        print("*** Can not import the MSAccess type libraries - tests skipped")
        return
    dbname = testAccess.CreateTestAccessDatabase()
    try:
        TestConnection(dbname)
    finally:
        os.unlink(dbname)


if __name__ == "__main__":
    Test()
