# 046327.python.serviceEvents.line1.comment A Demo of a service that takes advantage of the additional notifications
# 046328.python.serviceEvents.line2.comment available in later Windows versions.

# 046329.python.serviceEvents.line4.comment Note that all output is written as event log entries - so you must install
# 046330.python.serviceEvents.line5.comment and start the service, then look at the event log for messages as events
# 046331.python.serviceEvents.line6.comment are generated.

# 046332.python.serviceEvents.line8.comment Events are generated for USB device insertion and removal, power state
# 046333.python.serviceEvents.line9.comment changes and hardware profile events - so try putting your computer to
# 046334.python.serviceEvents.line10.comment sleep and waking it, inserting a memory stick, etc then check the event log

# 046335.python.serviceEvents.line12.comment Most event notification support lives around win32gui
import servicemanager
import win32con
import win32event
import win32gui
import win32gui_struct
import win32service
import win32serviceutil

GUID_DEVINTERFACE_USB_DEVICE = "{A5DCBF10-6530-11D2-901F-00C04FB951ED}"


class EventDemoService(win32serviceutil.ServiceFramework):
    _svc_name_ = "PyServiceEventDemo"
    _svc_display_name_ = "Python Service Event Demo"
    _svc_description_ = (
        "Demonstrates a Python service which takes advantage of the extra notifications"
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        # 046336.python.serviceEvents.line34.comment register for a device notification - we pass our service handle
        # 046337.python.serviceEvents.line35.comment instead of a window handle.
        filter = win32gui_struct.PackDEV_BROADCAST_DEVICEINTERFACE(
            GUID_DEVINTERFACE_USB_DEVICE
        )
        self.hdn = win32gui.RegisterDeviceNotification(
            self.ssh, filter, win32con.DEVICE_NOTIFY_SERVICE_HANDLE
        )

    # 046338.python.serviceEvents.line43.comment Override the base class so we can accept additional events.
    def GetAcceptedControls(self):
        # 046339.python.serviceEvents.line45.comment say we accept them all.
        rc = win32serviceutil.ServiceFramework.GetAcceptedControls(self)
        rc |= (
            win32service.SERVICE_ACCEPT_PARAMCHANGE
            | win32service.SERVICE_ACCEPT_NETBINDCHANGE
            | win32service.SERVICE_CONTROL_DEVICEEVENT
            | win32service.SERVICE_ACCEPT_HARDWAREPROFILECHANGE
            | win32service.SERVICE_ACCEPT_POWEREVENT
            | win32service.SERVICE_ACCEPT_SESSIONCHANGE
        )
        return rc

    # 046340.python.serviceEvents.line57.comment All extra events are sent via SvcOtherEx (SvcOther remains as a
    # 046341.python.serviceEvents.line58.comment function taking only the first args for backwards compat)
    def SvcOtherEx(self, control, event_type, data):
        # 046342.python.serviceEvents.line60.comment This is only showing a few of the extra events - see the MSDN
        # 046343.python.serviceEvents.line61.comment docs for "HandlerEx callback" for more info.
        if control == win32service.SERVICE_CONTROL_DEVICEEVENT:
            info = win32gui_struct.UnpackDEV_BROADCAST(data)
            msg = f"A device event occurred: {event_type:x} - {info}"
        elif control == win32service.SERVICE_CONTROL_HARDWAREPROFILECHANGE:
            msg = f"A hardware profile changed: type={event_type}, data={data}"
        elif control == win32service.SERVICE_CONTROL_POWEREVENT:
            msg = "A power event: setting %s" % data
        elif control == win32service.SERVICE_CONTROL_SESSIONCHANGE:
            # 046344.python.serviceEvents.line70.comment data is a single elt tuple, but this could potentially grow
            # 046345.python.serviceEvents.line71.comment in the future if the win32 struct does
            msg = f"Session event: type={event_type}, data={data}"
        else:
            msg = "Other event: code=%d, type=%s, data=%s" % (control, event_type, data)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            0xF000,  #  generic message
            (msg, ""),
        )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # 046347.python.serviceEvents.line87.comment do nothing at all - just wait to be stopped
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        # 046348.python.serviceEvents.line89.comment Write a stop message.
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, ""),
        )


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(EventDemoService)
