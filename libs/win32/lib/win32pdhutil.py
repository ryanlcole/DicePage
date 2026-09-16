"""Utilities for the win32 Performance Data Helper module

Example:
  To get a single bit of data:
  >>> import win32pdhutil
  >>> win32pdhutil.GetPerformanceAttributes("Memory", "Available Bytes")
  6053888
  >>> win32pdhutil.FindPerformanceAttributesByName("python", counter="Virtual Bytes")
  [22278144]

  First example returns data which is not associated with any specific instance.

  The second example reads data for a specific instance - hence the list return -
  it would return one result for each instance of Python running.

  In general, it can be tricky finding exactly the "name" of the data you wish to query.
  Although you can use <om win32pdh.EnumObjectItems>(None,None,(eg)"Memory", -1) to do this,
  the easiest way is often to simply use PerfMon to find out the names.
"""

from __future__ import annotations

import time

import win32pdh

error = win32pdh.error  # Re-exported alias

# 047500.python.win32pdhutil.line29.comment Handle some localization issues.
# 047501.python.win32pdhutil.line30.comment see https://www.betaarchive.com/wiki/index.php?title=Microsoft_KB_Archive/287159
# 047502.python.win32pdhutil.line31.comment Build a map of english_counter_name: counter_id
counter_english_map: dict[str, int] = {}


def find_pdh_counter_localized_name(english_name, machine_name=None):
    if not counter_english_map:
        import win32api
        import win32con

        counter_reg_value = win32api.RegQueryValueEx(
            win32con.HKEY_PERFORMANCE_DATA, "Counter 009"
        )
        counter_list = counter_reg_value[0]
        for i in range(0, len(counter_list) - 1, 2):
            try:
                counter_id = int(counter_list[i])
            except ValueError:
                continue
            counter_english_map[counter_list[i + 1].lower()] = counter_id
    return win32pdh.LookupPerfNameByIndex(
        machine_name, counter_english_map[english_name.lower()]
    )


def GetPerformanceAttributes(
    object, counter, instance=None, inum=-1, format=win32pdh.PDH_FMT_LONG, machine=None
):
    # 047503.python.win32pdhutil.line58.comment NOTE: Many counters require 2 samples to give accurate results,
    # 047504.python.win32pdhutil.line59.comment including "% Processor Time" (as by definition, at any instant, a
    # 047505.python.win32pdhutil.line60.comment thread's CPU usage is either 0 or 100).  To read counters like this,
    # 047506.python.win32pdhutil.line61.comment you should copy this function, but keep the counter open, and call
    # 047507.python.win32pdhutil.line62.comment CollectQueryData() each time you need to know.
    # 047508.python.win32pdhutil.line63.comment See https://www.betaarchive.com/wiki/index.php?title=Microsoft_KB_Archive/262938
    # 047509.python.win32pdhutil.line64.comment and https://web.archive.org/web/20040926105842/http://msdn.microsoft.com:80/library/en-us/dnperfmo/html/perfmonpt2.asp
    # 047510.python.win32pdhutil.line65.comment My older explanation for this was that the "AddCounter" process forced
    # 047511.python.win32pdhutil.line66.comment the CPU to 100%, but the above makes more sense :)
    path = win32pdh.MakeCounterPath((machine, object, instance, None, inum, counter))
    hq = win32pdh.OpenQuery()
    try:
        hc = win32pdh.AddCounter(hq, path)
        try:
            win32pdh.CollectQueryData(hq)
            type, val = win32pdh.GetFormattedCounterValue(hc, format)
            return val
        finally:
            win32pdh.RemoveCounter(hc)
    finally:
        win32pdh.CloseQuery(hq)


def FindPerformanceAttributesByName(
    instanceName,
    object=None,
    counter=None,
    format=win32pdh.PDH_FMT_LONG,
    machine=None,
    bRefresh=0,
):
    """Find performance attributes by (case insensitive) instance name.

    Given a process name, return a list with the requested attributes.
    Most useful for returning a tuple of PIDs given a process name.
    """
    if object is None:
        object = find_pdh_counter_localized_name("Process", machine)
    if counter is None:
        counter = find_pdh_counter_localized_name("ID Process", machine)
    if bRefresh:  # PDH docs say this is how you do a refresh.
        win32pdh.EnumObjects(None, machine, 0, 1)
    instanceName = instanceName.lower()
    items, instances = win32pdh.EnumObjectItems(None, None, object, -1)
    # 047513.python.win32pdhutil.line102.comment Track multiple instances.
    instance_dict = {}
    for instance in instances:
        try:
            instance_dict[instance] += 1
        except KeyError:
            instance_dict[instance] = 0

    ret = []
    for instance, max_instances in instance_dict.items():
        for inum in range(max_instances + 1):
            if instance.lower() == instanceName:
                ret.append(
                    GetPerformanceAttributes(
                        object, counter, instance, inum, format, machine
                    )
                )
    return ret


def ShowAllProcesses():
    object = find_pdh_counter_localized_name("Process")
    items, instances = win32pdh.EnumObjectItems(
        None, None, object, win32pdh.PERF_DETAIL_WIZARD
    )
    # 047514.python.win32pdhutil.line127.comment Need to track multiple instances of the same name.
    instance_dict = {}
    for instance in instances:
        try:
            instance_dict[instance] += 1
        except KeyError:
            instance_dict[instance] = 0

    # 047515.python.win32pdhutil.line135.comment Bit of a hack to get useful info.
    items = [find_pdh_counter_localized_name("ID Process")] + items[:5]
    print("Process Name", ",".join(items))
    for instance, max_instances in instance_dict.items():
        for inum in range(max_instances + 1):
            hq = win32pdh.OpenQuery()
            hcs = []
            for item in items:
                path = win32pdh.MakeCounterPath(
                    (None, object, instance, None, inum, item)
                )
                hcs.append(win32pdh.AddCounter(hq, path))
            win32pdh.CollectQueryData(hq)
            # 047516.python.win32pdhutil.line148.comment as per https://www.betaarchive.com/wiki/index.php?title=Microsoft_KB_Archive/262938
            # 047517.python.win32pdhutil.line149.comment some "%" based  counters need two collections
            time.sleep(0.01)
            win32pdh.CollectQueryData(hq)
            print("%-15s\t" % (instance[:15]), end=" ")
            for hc in hcs:
                type, val = win32pdh.GetFormattedCounterValue(hc, win32pdh.PDH_FMT_LONG)
                print("%5d" % (val), end=" ")
                win32pdh.RemoveCounter(hc)
            print()
            win32pdh.CloseQuery(hq)


# 047518.python.win32pdhutil.line161.comment NOTE: This BrowseCallback doesn't seem to work on Vista for markh.
# 047519.python.win32pdhutil.line162.comment XXX - look at why!?
# 047520.python.win32pdhutil.line163.comment Some counters on Vista require elevation, and callback would previously
# 047521.python.win32pdhutil.line164.comment clear exceptions without printing them.
def BrowseCallBackDemo(counters):
    # 047522.python.win32pdhutil.line166.comment # BrowseCounters can now return multiple counter paths
    for counter in counters:
        (
            machine,
            object,
            instance,
            parentInstance,
            index,
            counterName,
        ) = win32pdh.ParseCounterPath(counter)

        result = GetPerformanceAttributes(
            object, counterName, instance, index, win32pdh.PDH_FMT_DOUBLE, machine
        )
        print("Value of '%s' is" % counter, result)
        print(
            "Added '%s' on object '%s' (machine %s), instance %s(%d)-parent of %s"
            % (counterName, object, machine, instance, index, parentInstance)
        )
    return 0


def browse(
    callback=BrowseCallBackDemo,
    title="Python Browser",
    level=win32pdh.PERF_DETAIL_WIZARD,
):
    win32pdh.BrowseCounters(None, 0, callback, level, title, ReturnMultiple=True)


if __name__ == "__main__":
    ShowAllProcesses()
    # 047523.python.win32pdhutil.line198.comment Show how to get a couple of attributes by name.
    counter = find_pdh_counter_localized_name("Virtual Bytes")
    print(
        "Virtual Bytes = ", FindPerformanceAttributesByName("python", counter=counter)
    )
    print(
        "Available Bytes = ",
        GetPerformanceAttributes(
            find_pdh_counter_localized_name("Memory"),
            find_pdh_counter_localized_name("Available Bytes"),
        ),
    )
    # 047524.python.win32pdhutil.line210.comment And a browser.
    print("Browsing for counters...")
    browse()
