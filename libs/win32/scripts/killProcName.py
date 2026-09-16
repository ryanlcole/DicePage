# 047987.python.killProcName.line1.comment Kills a process by process name
# 047988.python.killProcName.line2.comment
# 047989.python.killProcName.line3.comment Uses the Performance Data Helper to locate the PID, then kills it.
# 047990.python.killProcName.line4.comment Will only kill the process if there is only one process of that name
# 047991.python.killProcName.line5.comment (eg, attempting to kill "Python.exe" will only work if there is only
# 047992.python.killProcName.line6.comment one Python.exe running.  (Note that the current process does not
# 047993.python.killProcName.line7.comment count - ie, if Python.exe is hosting this script, you can still kill
# 047994.python.killProcName.line8.comment another Python.exe (as long as there is only one other Python.exe)

# 047995.python.killProcName.line10.comment Really just a demo for the win32pdh(util) module, which allows you
# 047996.python.killProcName.line11.comment to get all sorts of information about a running process and many
# 047997.python.killProcName.line12.comment other aspects of your system.

import sys

import win32api
import win32con
import win32pdhutil


def killProcName(procname):
    # 047998.python.killProcName.line22.comment Change suggested by Dan Knierim, who found that this performed a
    # 047999.python.killProcName.line23.comment "refresh", allowing us to kill processes created since this was run
    # 048000.python.killProcName.line24.comment for the first time.
    try:
        win32pdhutil.GetPerformanceAttributes("Process", "ID Process", procname)
    except:
        pass

    pids = win32pdhutil.FindPerformanceAttributesByName(procname)

    # 048001.python.killProcName.line32.comment If _my_ pid in there, remove it!
    try:
        pids.remove(win32api.GetCurrentProcessId())
    except ValueError:
        pass

    if len(pids) == 0:
        result = "Can't find %s" % procname
    elif len(pids) > 1:
        result = f"Found too many {procname}'s - pids=`{pids}`"
    else:
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pids[0])
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)
        result = ""

    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for procname in sys.argv[1:]:
            result = killProcName(procname)
            if result:
                print(result)
                print("Dumping all processes...")
                win32pdhutil.ShowAllProcesses()
            else:
                print("Killed %s" % procname)
    else:
        print("Usage: killProcName.py procname ...")
