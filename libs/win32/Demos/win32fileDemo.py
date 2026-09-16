# 046454.python.win32fileDemo.line1.comment This is a "demo" of win32file - it used to be more a test case than a
# 046455.python.win32fileDemo.line2.comment demo, so has been moved to the test directory.

import os

# 046456.python.win32fileDemo.line6.comment Please contribute your favourite simple little demo.
import win32api
import win32con
import win32file


# 046457.python.win32fileDemo.line12.comment A very simple demo - note that this does no more than you can do with
# 046458.python.win32fileDemo.line13.comment builtin Python file objects, so for something as simple as this, you
# 046459.python.win32fileDemo.line14.comment generally *should* use builtin Python objects.  Only use win32file etc
# 046460.python.win32fileDemo.line15.comment when you need win32 specific features not available in Python.
def SimpleFileDemo():
    testName = os.path.join(win32api.GetTempPath(), "win32file_demo_test_file")
    if os.path.exists(testName):
        os.unlink(testName)
    # 046461.python.win32fileDemo.line20.comment Open the file for writing.
    handle = win32file.CreateFile(
        testName, win32file.GENERIC_WRITE, 0, None, win32con.CREATE_NEW, 0, None
    )
    test_data = b"Hello\0there"
    win32file.WriteFile(handle, test_data)
    handle.Close()
    # 046462.python.win32fileDemo.line27.comment Open it for reading.
    handle = win32file.CreateFile(
        testName, win32file.GENERIC_READ, 0, None, win32con.OPEN_EXISTING, 0, None
    )
    rc, data = win32file.ReadFile(handle, 1024)
    handle.Close()
    if data == test_data:
        print("Successfully wrote and read a file")
    else:
        raise Exception("Got different data back???")
    os.unlink(testName)


if __name__ == "__main__":
    SimpleFileDemo()
