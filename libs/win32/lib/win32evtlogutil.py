"""Event Log Utilities - helper for win32evtlog.pyd"""

import win32api
import win32con
import win32evtlog
import winerror

error = win32api.error  # Re-exported alias (The error the evtlog module raises).
langid = win32api.MAKELANGID(win32con.LANG_NEUTRAL, win32con.SUBLANG_NEUTRAL)


def AddSourceToRegistry(
    appName,
    msgDLL=None,
    eventLogType="Application",
    eventLogFlags=None,
    categoryDLL=None,
    categoryCount=0,
):
    """Add a source of messages to the event log.

    Allows Python program to register a custom source of messages in the
    registry.  You must also provide the DLL name that has the message table, so the
    full message text appears in the event log.

    Note that the win32evtlog.pyd file has a number of string entries with just "%1"
    built in, so many Python programs can simply use this DLL.  Disadvantages are that
    you do not get language translation, and the full text is stored in the event log,
    blowing the size of the log up.
    """

    # 047286.python.win32evtlogutil.line32.comment When an application uses the RegisterEventSource or OpenEventLog
    # 047287.python.win32evtlogutil.line33.comment function to get a handle of an event log, the event logging service
    # 047288.python.win32evtlogutil.line34.comment searches for the specified source name in the registry. You can add a
    # 047289.python.win32evtlogutil.line35.comment new source name to the registry by opening a new registry subkey
    # 047290.python.win32evtlogutil.line36.comment under the Application key and adding registry values to the new
    # 047291.python.win32evtlogutil.line37.comment subkey.

    if msgDLL is None:
        msgDLL = win32evtlog.__file__
    # 047292.python.win32evtlogutil.line41.comment Create a new key for our application
    hkey = win32api.RegCreateKey(
        win32con.HKEY_LOCAL_MACHINE,
        f"SYSTEM\\CurrentControlSet\\Services\\EventLog\\{eventLogType}\\{appName}",
    )

    # 047293.python.win32evtlogutil.line47.comment Add the Event-ID message-file name to the subkey.
    win32api.RegSetValueEx(
        hkey,
        "EventMessageFile",  # value name \
        0,  # reserved \
        win32con.REG_EXPAND_SZ,  # value type \
        msgDLL,
    )

    # 047297.python.win32evtlogutil.line56.comment Set the supported types flags and add it to the subkey.
    if eventLogFlags is None:
        eventLogFlags = (
            win32evtlog.EVENTLOG_ERROR_TYPE
            | win32evtlog.EVENTLOG_WARNING_TYPE
            | win32evtlog.EVENTLOG_INFORMATION_TYPE
        )
    win32api.RegSetValueEx(
        hkey,  # subkey handle \
        "TypesSupported",  # value name \
        0,  # reserved \
        win32con.REG_DWORD,  # value type \
        eventLogFlags,
    )

    if categoryCount > 0:
        # 047302.python.win32evtlogutil.line72.comment Optionally, you can specify a message file that contains the categories
        if categoryDLL is None:
            categoryDLL = win32evtlog.__file__
        win32api.RegSetValueEx(
            hkey,  # subkey handle \
            "CategoryMessageFile",  # value name \
            0,  # reserved \
            win32con.REG_EXPAND_SZ,  # value type \
            categoryDLL,
        )

        win32api.RegSetValueEx(
            hkey,  # subkey handle \
            "CategoryCount",  # value name \
            0,  # reserved \
            win32con.REG_DWORD,  # value type \
            categoryCount,
        )
    win32api.RegCloseKey(hkey)


def RemoveSourceFromRegistry(appName, eventLogType="Application"):
    """Removes a source of messages from the event log."""

    # 047311.python.win32evtlogutil.line96.comment Delete our key
    try:
        win32api.RegDeleteKey(
            win32con.HKEY_LOCAL_MACHINE,
            f"SYSTEM\\CurrentControlSet\\Services\\EventLog\\{eventLogType}\\{appName}",
        )
    except win32api.error as exc:
        if exc.winerror != winerror.ERROR_FILE_NOT_FOUND:
            raise


def ReportEvent(
    appName,
    eventID,
    eventCategory=0,
    eventType=win32evtlog.EVENTLOG_ERROR_TYPE,
    strings=None,
    data=None,
    sid=None,
):
    """Report an event for a previously added event source."""
    # 047312.python.win32evtlogutil.line117.comment Get a handle to the Application event log
    hAppLog = win32evtlog.RegisterEventSource(None, appName)

    # 047313.python.win32evtlogutil.line120.comment Now report the event, which will add this event to the event log */
    win32evtlog.ReportEvent(
        hAppLog,  # event-log handle \
        eventType,
        eventCategory,
        eventID,
        sid,
        strings,
        data,
    )

    win32evtlog.DeregisterEventSource(hAppLog)


def FormatMessage(eventLogRecord, logType="Application"):
    """Given a tuple from ReadEventLog, and optionally where the event
    record came from, load the message, and process message inserts.

    Note that this function may raise win32api.error.  See also the
    function SafeFormatMessage which will return None if the message can
    not be processed.
    """

    # 047315.python.win32evtlogutil.line143.comment From the event log source name, we know the name of the registry
    # 047316.python.win32evtlogutil.line144.comment key to look under for the name of the message DLL that contains
    # 047317.python.win32evtlogutil.line145.comment the messages we need to extract with FormatMessage. So first get
    # 047318.python.win32evtlogutil.line146.comment the event log source name...
    keyName = "SYSTEM\\CurrentControlSet\\Services\\EventLog\\{}\\{}".format(
        logType,
        eventLogRecord.SourceName,
    )

    # 047319.python.win32evtlogutil.line152.comment Now open this key and get the EventMessageFile value, which is
    # 047320.python.win32evtlogutil.line153.comment the name of the message DLL.
    handle = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, keyName)
    try:
        dllNames = win32api.RegQueryValueEx(handle, "EventMessageFile")[0].split(";")
        # 047321.python.win32evtlogutil.line157.comment Win2k etc appear to allow multiple DLL names
        data = None
        for dllName in dllNames:
            try:
                # 047322.python.win32evtlogutil.line161.comment Expand environment variable strings in the message DLL path name,
                # 047323.python.win32evtlogutil.line162.comment in case any are there.
                dllName = win32api.ExpandEnvironmentStrings(dllName)

                dllHandle = win32api.LoadLibraryEx(
                    dllName, 0, win32con.LOAD_LIBRARY_AS_DATAFILE
                )
                try:
                    data = win32api.FormatMessageW(
                        win32con.FORMAT_MESSAGE_FROM_HMODULE,
                        dllHandle,
                        eventLogRecord.EventID,
                        langid,
                        eventLogRecord.StringInserts,
                    )
                finally:
                    win32api.FreeLibrary(dllHandle)
            except win32api.error:
                pass  # Not in this DLL - try the next
            if data is not None:
                break
    finally:
        win32api.RegCloseKey(handle)
    return data or ""  # Don't want "None" ever being returned.


def SafeFormatMessage(eventLogRecord, logType=None):
    """As for FormatMessage, except returns an error message if
    the message can not be processed.
    """
    if logType is None:
        logType = "Application"
    try:
        return FormatMessage(eventLogRecord, logType)
    except win32api.error:
        if eventLogRecord.StringInserts is None:
            desc = ""
        else:
            desc = ", ".join(eventLogRecord.StringInserts)
        return (
            "<The description for Event ID ( %d ) in Source ( %r ) could not be found. It contains the following insertion string(s):%r.>"
            % (
                winerror.HRESULT_CODE(eventLogRecord.EventID),
                eventLogRecord.SourceName,
                desc,
            )
        )


def FeedEventLogRecords(
    feeder, machineName=None, logName="Application", readFlags=None
):
    if readFlags is None:
        readFlags = (
            win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        )
    h = win32evtlog.OpenEventLog(machineName, logName)
    try:
        while 1:
            objects = win32evtlog.ReadEventLog(h, readFlags, 0)
            if not objects:
                break
            map(lambda item, feeder=feeder: feeder(*(item,)), objects)
    finally:
        win32evtlog.CloseEventLog(h)
