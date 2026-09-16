# 046116.python.rastest.line1.comment rastest.py - test/demonstrate the win32ras module.
# 046117.python.rastest.line2.comment Much of the code here contributed by Jethro Wright.

import os
import sys

import win32event
import win32ras

# 046118.python.rastest.line10.comment Build a little dictionary of RAS states to decent strings.
# 046119.python.rastest.line11.comment eg win32ras.RASCS_OpenPort -> "OpenPort"
stateMap = {
    val: name[6:] for name, val in win32ras.__dict__.items() if name[:6] == "RASCS_"
}

# 046120.python.rastest.line16.comment Use a lock so the callback can tell the main thread when it is finished.
callbackEvent = win32event.CreateEvent(None, 0, 0, None)


def Callback(hras, msg, state, error, exterror):
    # 046121.python.rastest.line21.comment print("Callback called with ", hras, msg, state, error, exterror)
    stateName = stateMap.get(state, "Unknown state?")
    print("Status is %s (%04lx), error code is %d" % (stateName, state, error))
    finished = state in [win32ras.RASCS_Connected]
    if finished:
        win32event.SetEvent(callbackEvent)
    if error != 0 or int(state) == win32ras.RASCS_Disconnected:
        # 046122.python.rastest.line28.comment we know for sure this is a good place to hangup....
        print("Detected call failure: %s" % win32ras.GetErrorString(error))
        HangUp(hras)
        win32event.SetEvent(callbackEvent)


def ShowConnections():
    print("All phone-book entries:")
    for (name,) in win32ras.EnumEntries():
        print(" ", name)
    print("Current Connections:")
    for con in win32ras.EnumConnections():
        print(" ", con)


def EditEntry(entryName):
    try:
        win32ras.EditPhonebookEntry(0, None, entryName)
    except win32ras.error as xxx_todo_changeme:
        (rc, function, msg) = xxx_todo_changeme.args
        print("Can not edit/find the RAS entry -", msg)


def HangUp(hras):
    # 046123.python.rastest.line52.comment trap potential, irrelevant errors from win32ras....
    try:
        win32ras.HangUp(hras)
    except:
        print("Tried to hang up gracefully on error, but didn't work....")
    return None


def Connect(entryName, bUseCallback):
    if bUseCallback:
        theCallback = Callback
        win32event.ResetEvent(callbackEvent)
    else:
        theCallback = None
    # 046124.python.rastest.line66.comment in order to *use* the username/password of a particular dun entry, one must
    # 046125.python.rastest.line67.comment explicitly get those params under win95....
    try:
        dp, b = win32ras.GetEntryDialParams(None, entryName)
    except:
        print("Couldn't find DUN entry: %s" % entryName)
    else:
        hras, rc = win32ras.Dial(
            None, None, (entryName, "", "", dp[3], dp[4], ""), theCallback
        )
        # 046126.python.rastest.line76.comment hras, rc = win32ras.Dial(None, None, (entryName, ),theCallback)
        # 046127.python.rastest.line77.comment print(hras, rc)
        if not bUseCallback and rc != 0:
            print("Could not dial the RAS connection:", win32ras.GetErrorString(rc))
            hras = HangUp(hras)
        # 046128.python.rastest.line81.comment don't wait here if there's no need to....
        elif (
            bUseCallback
            and win32event.WaitForSingleObject(callbackEvent, 60000)
            != win32event.WAIT_OBJECT_0
        ):
            print("Gave up waiting for the process to complete!")
            # 046129.python.rastest.line88.comment sdk docs state one must explcitly hangup, even if there's an error....
            try:
                cs = win32ras.GetConnectStatus(hras)
            except:
                # 046130.python.rastest.line92.comment on error, attempt a hang up anyway....
                hras = HangUp(hras)
            else:
                if int(cs[0]) == win32ras.RASCS_Disconnected:
                    hras = HangUp(hras)
    return hras, rc


def Disconnect(rasEntry):
    # 046131.python.rastest.line101.comment Need to find the entry
    name = rasEntry.lower()
    for hcon, entryName, devName, devType in win32ras.EnumConnections():
        if entryName.lower() == name:
            win32ras.HangUp(hcon)
            print("Disconnected from", rasEntry)
            break
    else:
        print("Could not find an open connection to", entryName)


usage = """
Usage: %s [-s] [-l] [-c connection] [-d connection]
-l : List phone-book entries and current connections.
-s : Show status while connecting/disconnecting (uses callbacks)
-c : Connect to the specified phonebook name.
-d : Disconnect from the specified phonebook name.
-e : Edit the specified phonebook entry.
"""


def main():
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], "slc:d:e:")
    except getopt.error as why:
        print(why)
        print(
            usage
            % (
                os.path.basename(
                    sys.argv[0],
                )
            )
        )
        return

    bCallback = 0
    if args or not opts:
        print(
            usage
            % (
                os.path.basename(
                    sys.argv[0],
                )
            )
        )
        return
    for opt, val in opts:
        if opt == "-s":
            bCallback = 1
        if opt == "-l":
            ShowConnections()
        if opt == "-c":
            hras, rc = Connect(val, bCallback)
            if hras is not None:
                print(f"hras: 0x{hras:8x}, rc: 0x{rc:04x}")
        if opt == "-d":
            Disconnect(val)
        if opt == "-e":
            EditEntry(val)


if __name__ == "__main__":
    main()
