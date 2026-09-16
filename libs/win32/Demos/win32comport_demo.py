# 046399.python.win32comport_demo.line1.comment This is a simple serial port terminal demo.
# 046400.python.win32comport_demo.line2.comment
# 046401.python.win32comport_demo.line3.comment Its primary purpose is to demonstrate the native serial port access offered via
# 046402.python.win32comport_demo.line4.comment win32file.

# 046403.python.win32comport_demo.line6.comment It uses 3 threads:
# 046404.python.win32comport_demo.line7.comment - The main thread, which cranks up the other 2 threads, then simply waits for them to exit.
# 046405.python.win32comport_demo.line8.comment - The user-input thread - blocks waiting for a keyboard character, and when found sends it
# 046406.python.win32comport_demo.line9.comment out the COM port.  If the character is Ctrl+C, it stops, signalling the COM port thread to stop.
# 046407.python.win32comport_demo.line10.comment - The COM port thread is simply listening for input on the COM port, and prints it to the screen.

# 046408.python.win32comport_demo.line12.comment This demo uses userlapped IO, so that none of the read or write operations actually block (however,
# 046409.python.win32comport_demo.line13.comment in this sample, the very next thing we do _is_ block - so it shows off the concepts even though it
# 046410.python.win32comport_demo.line14.comment doesn't exploit them.

import msvcrt  # For the getch() function.
import sys
import threading

import win32con  # constants.
from win32event import (  # We use events and the WaitFor[Multiple]Objects functions.
    INFINITE,
    WAIT_OBJECT_0,
    CreateEvent,
    SetEvent,
    WaitForMultipleObjects,
    WaitForSingleObject,
)
from win32file import (  # The base COM port and file IO functions.
    CBR_115200,
    EV_RXCHAR,
    NOPARITY,
    ONESTOPBIT,
    OVERLAPPED,
    PURGE_RXABORT,
    PURGE_RXCLEAR,
    PURGE_TXABORT,
    PURGE_TXCLEAR,
    ClearCommError,
    CreateFile,
    GetCommModemStatus,
    GetCommState,
    PurgeComm,
    ReadFile,
    SetCommMask,
    SetCommState,
    SetCommTimeouts,
    SetupComm,
    WaitCommEvent,
    WriteFile,
    error,
)


def FindModem():
    # 046415.python.win32comport_demo.line56.comment Snoop over the comports, seeing if it is likely we have a modem.
    for i in range(1, 5):
        port = "COM%d" % (i,)
        try:
            handle = CreateFile(
                port,
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                0,  # exclusive access
                None,  # no security
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None,
            )
            # 046418.python.win32comport_demo.line69.comment It appears that an available COM port will always success here,
            # 046419.python.win32comport_demo.line70.comment just return 0 for the status flags.  We only care that it has _any_ status
            # 046420.python.win32comport_demo.line71.comment flags (and therefore probably a real modem)
            if GetCommModemStatus(handle) != 0:
                return port
        except error:
            pass  # No port, or modem status failed.
    return None


# 046422.python.win32comport_demo.line79.comment A basic synchronous COM port file-like object
class SerialTTY:
    def __init__(self, port):
        if isinstance(port, int):
            port = "COM%d" % (port,)
        self.handle = CreateFile(
            port,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,  # exclusive access
            None,  # no security
            win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_OVERLAPPED,
            None,
        )
        # 046425.python.win32comport_demo.line93.comment Tell the port we want a notification on each char.
        SetCommMask(self.handle, EV_RXCHAR)
        # 046426.python.win32comport_demo.line95.comment Setup a 4k buffer
        SetupComm(self.handle, 4096, 4096)
        # 046427.python.win32comport_demo.line97.comment Remove anything that was there
        PurgeComm(
            self.handle, PURGE_TXABORT | PURGE_RXABORT | PURGE_TXCLEAR | PURGE_RXCLEAR
        )
        # 046428.python.win32comport_demo.line101.comment Setup for overlapped IO.
        timeouts = 0xFFFFFFFF, 0, 1000, 0, 1000
        SetCommTimeouts(self.handle, timeouts)
        # 046429.python.win32comport_demo.line104.comment Setup the connection info.
        dcb = GetCommState(self.handle)
        dcb.BaudRate = CBR_115200
        dcb.ByteSize = 8
        dcb.Parity = NOPARITY
        dcb.StopBits = ONESTOPBIT
        SetCommState(self.handle, dcb)
        print(f"Connected to {port} at {dcb.BaudRate} baud")

    def _UserInputReaderThread(self):
        overlapped = OVERLAPPED()
        overlapped.hEvent = CreateEvent(None, 1, 0, None)
        try:
            while 1:
                ch = msvcrt.getch()
                if ord(ch) == 3:
                    break
                WriteFile(self.handle, ch, overlapped)
                # 046430.python.win32comport_demo.line122.comment Wait for the write to complete.
                WaitForSingleObject(overlapped.hEvent, INFINITE)
        finally:
            SetEvent(self.eventStop)

    def _ComPortThread(self):
        overlapped = OVERLAPPED()
        overlapped.hEvent = CreateEvent(None, 1, 0, None)
        while 1:
            # 046431.python.win32comport_demo.line131.comment XXX - note we could _probably_ just use overlapped IO on the win32file.ReadFile() statement
            # 046432.python.win32comport_demo.line132.comment XXX but this tests the COM stuff!
            rc, mask = WaitCommEvent(self.handle, overlapped)
            if rc == 0:  # Character already ready!
                SetEvent(overlapped.hEvent)
            rc = WaitForMultipleObjects(
                [overlapped.hEvent, self.eventStop], 0, INFINITE
            )
            if rc == WAIT_OBJECT_0:
                # 046434.python.win32comport_demo.line140.comment Some input - read and print it
                flags, comstat = ClearCommError(self.handle)
                rc, data = ReadFile(self.handle, comstat.cbInQue, overlapped)
                WaitForSingleObject(overlapped.hEvent, INFINITE)
                sys.stdout.write(data)
            else:
                # 046435.python.win32comport_demo.line146.comment Stop the thread!
                # 046436.python.win32comport_demo.line147.comment Just incase the user input thread uis still going, close it
                sys.stdout.close()
                break

    def Run(self):
        self.eventStop = CreateEvent(None, 0, 0, None)
        # 046437.python.win32comport_demo.line153.comment Start the reader and writer threads.
        user_thread = threading.Thread(target=self._UserInputReaderThread)
        user_thread.start()
        com_thread = threading.Thread(target=self._ComPortThread)
        com_thread.start()
        user_thread.join()
        com_thread.join()


if __name__ == "__main__":
    print("Serial port terminal demo - press Ctrl+C to exit")
    if len(sys.argv) <= 1:
        port = FindModem()
        if port is None:
            print("No COM port specified, and no modem could be found")
            print("Please re-run this script with the name of a COM port (eg COM3)")
            sys.exit(1)
    else:
        port = sys.argv[1]

    tty = SerialTTY(port)
    tty.Run()
