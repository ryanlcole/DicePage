# 047585.python.win32serviceutil.line1.comment General purpose service utilities, both for standard Python scripts,
# 047586.python.win32serviceutil.line2.comment and for for Python programs which run as services...
# 047587.python.win32serviceutil.line3.comment
# 047588.python.win32serviceutil.line4.comment Note that most utility functions here will raise win32api.error's
# 047589.python.win32serviceutil.line5.comment (which is win32service.error, pywintypes.error, etc)
# 047590.python.win32serviceutil.line6.comment when things go wrong - eg, not enough permissions to hit the
# 047591.python.win32serviceutil.line7.comment registry etc.

import importlib.machinery
import os
import sys
import warnings

import pywintypes
import win32api
import win32con
import win32service
import winerror

error = RuntimeError  # Re-exported alias


# 047593.python.win32serviceutil.line23.comment Returns the full path to an executable for hosting a Python service - typically
# 047594.python.win32serviceutil.line24.comment 'pythonservice.exe'
# 047595.python.win32serviceutil.line25.comment * If you pass a param and it exists as a file, you'll get the abs path back
# 047596.python.win32serviceutil.line26.comment * Otherwise we'll use the param instead of 'pythonservice.exe', and we will
# 047597.python.win32serviceutil.line27.comment look for it.
def LocatePythonServiceExe(exe=None):
    if not exe and hasattr(sys, "frozen"):
        # 047598.python.win32serviceutil.line30.comment If py2exe etc calls this with no exe, default is current exe,
        # 047599.python.win32serviceutil.line31.comment and all setup is their problem :)
        return sys.executable

    if exe and os.path.isfile(exe):
        return win32api.GetFullPathName(exe)

    suffix = "_d" if "_d.pyd" in importlib.machinery.EXTENSION_SUFFIXES else ""

    # 047600.python.win32serviceutil.line39.comment We are confused if we aren't now looking for our default. But if that
    # 047601.python.win32serviceutil.line40.comment exists as specified we assume it's good.
    exe = f"pythonservice{suffix}.exe"
    if os.path.isfile(exe):
        return win32api.GetFullPathName(exe)

    # 047602.python.win32serviceutil.line45.comment Now we are searching for the .exe
    # 047603.python.win32serviceutil.line46.comment We are going to want it here.
    correct = os.path.join(sys.exec_prefix, exe)
    # 047604.python.win32serviceutil.line48.comment Even if that file already exists, we copy the one installed by pywin32
    # 047605.python.win32serviceutil.line49.comment in-case it was upgraded.
    # 047606.python.win32serviceutil.line50.comment pywin32 installed it next to win32service.pyd (but we can't run it from there)
    maybe = os.path.join(os.path.dirname(win32service.__file__), exe)
    if os.path.exists(maybe):
        print(f"moving host exe '{maybe}' -> '{correct}'")
        # 047607.python.win32serviceutil.line54.comment Handle case where MoveFile() fails. Particularly if destination file
        # 047608.python.win32serviceutil.line55.comment has a resource lock and can't be replaced by src file
        try:
            win32api.MoveFileEx(maybe, correct, win32con.MOVEFILE_REPLACE_EXISTING)
        except win32api.error as exc:
            print(f"Failed to move host exe '{exc}'")

    if not os.path.exists(correct):
        raise error(f"Can't find '{correct}'")

    # 047609.python.win32serviceutil.line64.comment If pywintypes.dll isn't next to us, or at least next to pythonXX.dll,
    # 047610.python.win32serviceutil.line65.comment there's a good chance the service will not run. That's usually copied by
    # 047611.python.win32serviceutil.line66.comment `pywin32_postinstall`, but putting it next to the python DLL seems reasonable.
    # 047612.python.win32serviceutil.line67.comment (Unlike the .exe above, we don't unconditionally copy this, and possibly
    # 047613.python.win32serviceutil.line68.comment copy it to a different place. Doesn't seem a good reason for that!?)
    python_dll = win32api.GetModuleFileName(sys.dllhandle)
    pyw = f"pywintypes{sys.version_info.major}{sys.version_info.minor}{suffix}.dll"
    correct_pyw = os.path.join(os.path.dirname(python_dll), pyw)

    if not os.path.exists(correct_pyw):
        print(f"copying helper dll '{pywintypes.__file__}' -> '{correct_pyw}'")
        win32api.CopyFile(pywintypes.__file__, correct_pyw)

    return correct


def _GetServiceShortName(longName):
    # 047614.python.win32serviceutil.line81.comment looks up a services name
    # 047615.python.win32serviceutil.line82.comment from the display name
    # 047616.python.win32serviceutil.line83.comment Thanks to Andy McKay for this code.
    access = (
        win32con.KEY_READ | win32con.KEY_ENUMERATE_SUB_KEYS | win32con.KEY_QUERY_VALUE
    )
    hkey = win32api.RegOpenKey(
        win32con.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services", 0, access
    )
    num = win32api.RegQueryInfoKey(hkey)[0]
    longName = longName.lower()
    # 047617.python.win32serviceutil.line92.comment loop through number of subkeys
    for x in range(0, num):
        # 047618.python.win32serviceutil.line94.comment find service name, open subkey
        svc = win32api.RegEnumKey(hkey, x)
        skey = win32api.RegOpenKey(hkey, svc, 0, access)
        try:
            # 047619.python.win32serviceutil.line98.comment find display name
            thisName = str(win32api.RegQueryValueEx(skey, "DisplayName")[0])
            if thisName.lower() == longName:
                return svc
        except win32api.error:
            # 047620.python.win32serviceutil.line103.comment in case there is no key called DisplayName
            pass
    return None


# 047621.python.win32serviceutil.line108.comment Open a service given either it's long or short name.
def SmartOpenService(hscm, name, access):
    try:
        return win32service.OpenService(hscm, name, access)
    except win32api.error as details:
        if details.winerror not in [
            winerror.ERROR_SERVICE_DOES_NOT_EXIST,
            winerror.ERROR_INVALID_NAME,
        ]:
            raise
    name = win32service.GetServiceKeyName(hscm, name)
    return win32service.OpenService(hscm, name, access)


def LocateSpecificServiceExe(serviceName):
    # 047622.python.win32serviceutil.line123.comment Return the .exe name of any service.
    hkey = win32api.RegOpenKey(
        win32con.HKEY_LOCAL_MACHINE,
        "SYSTEM\\CurrentControlSet\\Services\\%s" % (serviceName),
        0,
        win32con.KEY_QUERY_VALUE,
    )
    try:
        return win32api.RegQueryValueEx(hkey, "ImagePath")[0]
    finally:
        hkey.Close()


def InstallPerfmonForService(serviceName, iniName, dllName=None):
    # 047623.python.win32serviceutil.line137.comment If no DLL name, look it up in the INI file name
    if not dllName:  # May be empty string!
        dllName = win32api.GetProfileVal("Python", "dll", "", iniName)
    # 047625.python.win32serviceutil.line140.comment Still not found - look for the standard one in the same dir as win32service.pyd
    if not dllName:
        try:
            tryName = os.path.join(
                os.path.split(win32service.__file__)[0], "perfmondata.dll"
            )
            if os.path.isfile(tryName):
                dllName = tryName
        except AttributeError:
            # 047626.python.win32serviceutil.line149.comment Frozen app? - anyway, can't find it!
            pass
    if not dllName:
        raise ValueError("The name of the performance DLL must be available")
    dllName = win32api.GetFullPathName(dllName)
    # 047627.python.win32serviceutil.line154.comment Now setup all the required "Performance" entries.
    hkey = win32api.RegOpenKey(
        win32con.HKEY_LOCAL_MACHINE,
        "SYSTEM\\CurrentControlSet\\Services\\%s" % (serviceName),
        0,
        win32con.KEY_ALL_ACCESS,
    )
    try:
        subKey = win32api.RegCreateKey(hkey, "Performance")
        try:
            win32api.RegSetValueEx(subKey, "Library", 0, win32con.REG_SZ, dllName)
            win32api.RegSetValueEx(
                subKey, "Open", 0, win32con.REG_SZ, "OpenPerformanceData"
            )
            win32api.RegSetValueEx(
                subKey, "Close", 0, win32con.REG_SZ, "ClosePerformanceData"
            )
            win32api.RegSetValueEx(
                subKey, "Collect", 0, win32con.REG_SZ, "CollectPerformanceData"
            )
        finally:
            win32api.RegCloseKey(subKey)
    finally:
        win32api.RegCloseKey(hkey)
    # 047628.python.win32serviceutil.line178.comment Now do the "Lodctr" thang...

    try:
        import perfmon

        path, fname = os.path.split(iniName)
        oldPath = os.getcwd()
        if path:
            os.chdir(path)
        try:
            perfmon.LoadPerfCounterTextStrings("python.exe " + fname)
        finally:
            os.chdir(oldPath)
    except win32api.error as details:
        print("The service was installed OK, but the performance monitor")
        print("data could not be loaded.", details)


def _GetCommandLine(exeName, exeArgs):
    if exeArgs is not None:
        return exeName + " " + exeArgs
    else:
        return exeName


def InstallService(
    pythonClassString,
    serviceName,
    displayName,
    startType=None,
    errorControl=None,
    bRunInteractive=0,
    serviceDeps=None,
    userName=None,
    password=None,
    exeName=None,
    perfMonIni=None,
    perfMonDll=None,
    exeArgs=None,
    description=None,
    delayedstart=None,
):
    # 047629.python.win32serviceutil.line220.comment Handle the default arguments.
    if startType is None:
        startType = win32service.SERVICE_DEMAND_START
    serviceType = win32service.SERVICE_WIN32_OWN_PROCESS
    if bRunInteractive:
        serviceType |= win32service.SERVICE_INTERACTIVE_PROCESS
    if errorControl is None:
        errorControl = win32service.SERVICE_ERROR_NORMAL

    exeName = '"%s"' % LocatePythonServiceExe(exeName)
    commandLine = _GetCommandLine(exeName, exeArgs)
    hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    try:
        hs = win32service.CreateService(
            hscm,
            serviceName,
            displayName,
            win32service.SERVICE_ALL_ACCESS,  # desired access
            serviceType,  # service type
            startType,
            errorControl,  # error control type
            commandLine,
            None,
            0,
            serviceDeps,
            userName,
            password,
        )
        if description is not None:
            try:
                win32service.ChangeServiceConfig2(
                    hs, win32service.SERVICE_CONFIG_DESCRIPTION, description
                )
            except NotImplementedError:
                pass  ## ChangeServiceConfig2 and description do not exist on NT
        if delayedstart is not None:
            try:
                win32service.ChangeServiceConfig2(
                    hs,
                    win32service.SERVICE_CONFIG_DELAYED_AUTO_START_INFO,
                    delayedstart,
                )
            except (win32service.error, NotImplementedError):
                # 047634.python.win32serviceutil.line263.comment # delayed start only exists on Vista and later - warn only when trying to set delayed to True
                warnings.warn(
                    "Delayed Start not available on this system", stacklevel=2
                )
        win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)
    InstallPythonClassString(pythonClassString, serviceName)
    # 047635.python.win32serviceutil.line271.comment If I have performance monitor info to install, do that.
    if perfMonIni is not None:
        InstallPerfmonForService(serviceName, perfMonIni, perfMonDll)


def ChangeServiceConfig(
    pythonClassString,
    serviceName,
    startType=None,
    errorControl=None,
    bRunInteractive=0,
    serviceDeps=None,
    userName=None,
    password=None,
    exeName=None,
    displayName=None,
    perfMonIni=None,
    perfMonDll=None,
    exeArgs=None,
    description=None,
    delayedstart=None,
):
    # 047636.python.win32serviceutil.line293.comment Before doing anything, remove any perfmon counters.
    try:
        import perfmon

        perfmon.UnloadPerfCounterTextStrings("python.exe " + serviceName)
    except (ImportError, win32api.error):
        pass

    # 047637.python.win32serviceutil.line301.comment The EXE location may have changed
    exeName = '"%s"' % LocatePythonServiceExe(exeName)

    # 047638.python.win32serviceutil.line304.comment Handle the default arguments.
    if startType is None:
        startType = win32service.SERVICE_NO_CHANGE
    if errorControl is None:
        errorControl = win32service.SERVICE_NO_CHANGE

    hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    serviceType = win32service.SERVICE_WIN32_OWN_PROCESS
    if bRunInteractive:
        serviceType |= win32service.SERVICE_INTERACTIVE_PROCESS
    commandLine = _GetCommandLine(exeName, exeArgs)
    try:
        hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
        try:
            win32service.ChangeServiceConfig(
                hs,
                serviceType,  # service type
                startType,
                errorControl,  # error control type
                commandLine,
                None,
                0,
                serviceDeps,
                userName,
                password,
                displayName,
            )
            if description is not None:
                try:
                    win32service.ChangeServiceConfig2(
                        hs, win32service.SERVICE_CONFIG_DESCRIPTION, description
                    )
                except NotImplementedError:
                    pass  ## ChangeServiceConfig2 and description do not exist on NT
            if delayedstart is not None:
                try:
                    win32service.ChangeServiceConfig2(
                        hs,
                        win32service.SERVICE_CONFIG_DELAYED_AUTO_START_INFO,
                        delayedstart,
                    )
                except (win32service.error, NotImplementedError):
                    # 047642.python.win32serviceutil.line346.comment # Delayed start only exists on Vista and later.  On Nt, will raise NotImplementedError since ChangeServiceConfig2
                    # 047643.python.win32serviceutil.line347.comment # doensn't exist.  On Win2k and XP, will fail with ERROR_INVALID_LEVEL
                    # 047644.python.win32serviceutil.line348.comment # Warn only if trying to set delayed to True
                    if delayedstart:
                        warnings.warn(
                            "Delayed Start not available on this system", stacklevel=2
                        )
        finally:
            win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)
    InstallPythonClassString(pythonClassString, serviceName)
    # 047645.python.win32serviceutil.line358.comment If I have performance monitor info to install, do that.
    if perfMonIni is not None:
        InstallPerfmonForService(serviceName, perfMonIni, perfMonDll)


def InstallPythonClassString(pythonClassString, serviceName):
    # 047646.python.win32serviceutil.line364.comment Now setup our Python specific entries.
    if pythonClassString:
        key = win32api.RegCreateKey(
            win32con.HKEY_LOCAL_MACHINE,
            "System\\CurrentControlSet\\Services\\%s\\PythonClass" % serviceName,
        )
        try:
            win32api.RegSetValue(key, None, win32con.REG_SZ, pythonClassString)
        finally:
            win32api.RegCloseKey(key)


# 047647.python.win32serviceutil.line376.comment Utility functions for Services, to allow persistant properties.
def SetServiceCustomOption(serviceName, option, value):
    try:
        serviceName = serviceName._svc_name_
    except AttributeError:
        pass
    key = win32api.RegCreateKey(
        win32con.HKEY_LOCAL_MACHINE,
        "System\\CurrentControlSet\\Services\\%s\\Parameters" % serviceName,
    )
    try:
        if isinstance(value, int):
            win32api.RegSetValueEx(key, option, 0, win32con.REG_DWORD, value)
        else:
            win32api.RegSetValueEx(key, option, 0, win32con.REG_SZ, value)
    finally:
        win32api.RegCloseKey(key)


def GetServiceCustomOption(serviceName, option, defaultValue=None):
    # 047648.python.win32serviceutil.line396.comment First param may also be a service class/instance.
    # 047649.python.win32serviceutil.line397.comment This allows services to pass "self"
    try:
        serviceName = serviceName._svc_name_
    except AttributeError:
        pass
    key = win32api.RegCreateKey(
        win32con.HKEY_LOCAL_MACHINE,
        "System\\CurrentControlSet\\Services\\%s\\Parameters" % serviceName,
    )
    try:
        try:
            return win32api.RegQueryValueEx(key, option)[0]
        except win32api.error:  # No value.
            return defaultValue
    finally:
        win32api.RegCloseKey(key)


def RemoveService(serviceName):
    try:
        import perfmon

        perfmon.UnloadPerfCounterTextStrings("python.exe " + serviceName)
    except (ImportError, win32api.error):
        pass

    hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    try:
        hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
        win32service.DeleteService(hs)
        win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)

    import win32evtlogutil

    try:
        win32evtlogutil.RemoveSourceFromRegistry(serviceName)
    except win32api.error:
        pass


def ControlService(serviceName, code, machine=None):
    hscm = win32service.OpenSCManager(machine, None, win32service.SC_MANAGER_ALL_ACCESS)
    try:
        hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
        try:
            status = win32service.ControlService(hs, code)
        finally:
            win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)
    return status


def __FindSvcDeps(findName):
    dict = {}
    k = win32api.RegOpenKey(
        win32con.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services"
    )
    num = 0
    while 1:
        try:
            svc = win32api.RegEnumKey(k, num)
        except win32api.error:
            break
        num += 1
        sk = win32api.RegOpenKey(k, svc)
        try:
            deps, typ = win32api.RegQueryValueEx(sk, "DependOnService")
        except win32api.error:
            deps = ()
        for dep in deps:
            dep = dep.lower()
            dep_on = dict.get(dep, [])
            dep_on.append(svc)
            dict[dep] = dep_on

    return __ResolveDeps(findName, dict)


def __ResolveDeps(findName, dict):
    items = dict.get(findName.lower(), [])
    retList = []
    for svc in items:
        retList.insert(0, svc)
        retList = __ResolveDeps(svc, dict) + retList
    return retList


def WaitForServiceStatus(serviceName, status, waitSecs, machine=None):
    """Waits for the service to return the specified status.  You
    should have already requested the service to enter that state"""
    for i in range(waitSecs * 4):
        now_status = QueryServiceStatus(serviceName, machine)[1]
        if now_status == status:
            break
        win32api.Sleep(250)
    else:
        raise pywintypes.error(
            winerror.ERROR_SERVICE_REQUEST_TIMEOUT,
            "QueryServiceStatus",
            win32api.FormatMessage(winerror.ERROR_SERVICE_REQUEST_TIMEOUT)[:-2],
        )


def __StopServiceWithTimeout(hs, waitSecs=30):
    try:
        status = win32service.ControlService(hs, win32service.SERVICE_CONTROL_STOP)
    except pywintypes.error as exc:
        if exc.winerror != winerror.ERROR_SERVICE_NOT_ACTIVE:
            raise
    for i in range(waitSecs):
        status = win32service.QueryServiceStatus(hs)
        if status[1] == win32service.SERVICE_STOPPED:
            break
        win32api.Sleep(1000)
    else:
        raise pywintypes.error(
            winerror.ERROR_SERVICE_REQUEST_TIMEOUT,
            "ControlService",
            win32api.FormatMessage(winerror.ERROR_SERVICE_REQUEST_TIMEOUT)[:-2],
        )


def StopServiceWithDeps(serviceName, machine=None, waitSecs=30):
    # 047651.python.win32serviceutil.line523.comment Stop a service recursively looking for dependant services
    hscm = win32service.OpenSCManager(machine, None, win32service.SC_MANAGER_ALL_ACCESS)
    try:
        deps = __FindSvcDeps(serviceName)
        for dep in deps:
            hs = win32service.OpenService(hscm, dep, win32service.SERVICE_ALL_ACCESS)
            try:
                __StopServiceWithTimeout(hs, waitSecs)
            finally:
                win32service.CloseServiceHandle(hs)
        # 047652.python.win32serviceutil.line533.comment Now my service!
        hs = win32service.OpenService(
            hscm, serviceName, win32service.SERVICE_ALL_ACCESS
        )
        try:
            __StopServiceWithTimeout(hs, waitSecs)
        finally:
            win32service.CloseServiceHandle(hs)

    finally:
        win32service.CloseServiceHandle(hscm)


def StopService(serviceName, machine=None):
    return ControlService(serviceName, win32service.SERVICE_CONTROL_STOP, machine)


def StartService(serviceName, args=None, machine=None):
    hscm = win32service.OpenSCManager(machine, None, win32service.SC_MANAGER_ALL_ACCESS)
    try:
        hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
        try:
            win32service.StartService(hs, args)
        finally:
            win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)


def RestartService(serviceName, args=None, waitSeconds=30, machine=None):
    "Stop the service, and then start it again (with some tolerance for allowing it to stop.)"
    try:
        StopService(serviceName, machine)
    except pywintypes.error as exc:
        # 047653.python.win32serviceutil.line567.comment Allow only "service not running" error
        if exc.winerror != winerror.ERROR_SERVICE_NOT_ACTIVE:
            raise
    # 047654.python.win32serviceutil.line570.comment Give it a few goes, as the service may take time to stop
    for i in range(waitSeconds):
        try:
            StartService(serviceName, args, machine)
            break
        except pywintypes.error as exc:
            if exc.winerror != winerror.ERROR_SERVICE_ALREADY_RUNNING:
                raise
            win32api.Sleep(1000)
    else:
        print("Gave up waiting for the old service to stop!")


def _DebugCtrlHandler(evt):
    if evt in (win32con.CTRL_C_EVENT, win32con.CTRL_BREAK_EVENT):
        assert g_debugService
        print("Stopping debug service.")
        g_debugService.SvcStop()
        return True
    return False


def DebugService(cls, argv=[]):
    # 047655.python.win32serviceutil.line593.comment Run a service in "debug" mode.  Re-implements what pythonservice.exe
    # 047656.python.win32serviceutil.line594.comment does when it sees a "-debug" param.
    # 047657.python.win32serviceutil.line595.comment Currently only used by "frozen" (ie, py2exe) programs (but later may
    # 047658.python.win32serviceutil.line596.comment end up being used for all services should we ever remove
    # 047659.python.win32serviceutil.line597.comment pythonservice.exe)
    import servicemanager

    global g_debugService

    print(f"Debugging service {cls._svc_name_} - press Ctrl+C to stop.")
    servicemanager.Debugging(True)
    servicemanager.PrepareToHostSingle(cls)
    g_debugService = cls(argv)
    # 047660.python.win32serviceutil.line606.comment Setup a ctrl+c handler to simulate a "stop"
    win32api.SetConsoleCtrlHandler(_DebugCtrlHandler, True)
    try:
        g_debugService.SvcRun()
    finally:
        win32api.SetConsoleCtrlHandler(_DebugCtrlHandler, False)
        servicemanager.Debugging(False)
        g_debugService = None


def GetServiceClassString(cls, argv=None):
    if argv is None:
        argv = sys.argv
    import pickle

    modName = pickle.whichmodule(cls, cls.__name__)
    if modName == "__main__":
        try:
            fname = win32api.GetFullPathName(argv[0])
            path = os.path.split(fname)[0]
            # 047661.python.win32serviceutil.line626.comment Eaaaahhhh - sometimes this will be a short filename, which causes
            # 047662.python.win32serviceutil.line627.comment problems with 1.5.1 and the silly filename case rule.
            filelist = win32api.FindFiles(fname)
            # 047663.python.win32serviceutil.line629.comment win32api.FindFiles will not detect files in a zip or exe. If list is empty,
            # 047664.python.win32serviceutil.line630.comment skip the test and hope the file really exists.
            if len(filelist) != 0:
                # 047665.python.win32serviceutil.line632.comment Get the long name
                fname = os.path.join(path, filelist[0][8])
        except win32api.error:
            raise error(
                "Could not resolve the path name '%s' to a full path" % (argv[0])
            )
        modName = os.path.splitext(fname)[0]
    return modName + "." + cls.__name__


def QueryServiceStatus(serviceName, machine=None):
    hscm = win32service.OpenSCManager(machine, None, win32service.SC_MANAGER_CONNECT)
    try:
        hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_QUERY_STATUS)
        try:
            status = win32service.QueryServiceStatus(hs)
        finally:
            win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)
    return status


def usage():
    try:
        fname = os.path.split(sys.argv[0])[1]
    except:
        fname = sys.argv[0]
    print(
        "Usage: '%s [options] install|update|remove|start [...]|stop|restart [...]|debug [...]'"
        % fname
    )
    print("Options for 'install' and 'update' commands only:")
    print(" --username domain\\username : The Username the service is to run under")
    print(" --password password : The password for the username")
    print(
        " --startup [manual|auto|disabled|delayed] : How the service starts, default = manual"
    )
    print(" --interactive : Allow the service to interact with the desktop.")
    print(
        " --perfmonini file: .ini file to use for registering performance monitor data"
    )
    print(" --perfmondll file: .dll file to use when querying the service for")
    print("   performance data, default = perfmondata.dll")
    print("Options for 'start' and 'stop' commands only:")
    print(" --wait seconds: Wait for the service to actually start or stop.")
    print("                 If you specify --wait with the 'stop' option, the service")
    print("                 and all dependent services will be stopped, each waiting")
    print("                 the specified period.")
    sys.exit(1)


def HandleCommandLine(
    cls,
    serviceClassString=None,
    argv=None,
    customInstallOptions="",
    customOptionHandler=None,
):
    """Utility function allowing services to process the command line.

    Allows standard commands such as 'start', 'stop', 'debug', 'install' etc.

    Install supports 'standard' command line options prefixed with '--', such as
    --username, --password, etc.  In addition,
    the function allows custom command line options to be handled by the calling function.
    """
    err = 0

    if argv is None:
        argv = sys.argv

    if len(argv) <= 1:
        usage()

    serviceName = cls._svc_name_
    serviceDisplayName = cls._svc_display_name_
    if serviceClassString is None:
        serviceClassString = GetServiceClassString(cls)

    # 047666.python.win32serviceutil.line712.comment Pull apart the command line
    import getopt

    try:
        opts, args = getopt.getopt(
            argv[1:],
            customInstallOptions,
            [
                "password=",
                "username=",
                "startup=",
                "perfmonini=",
                "perfmondll=",
                "interactive",
                "wait=",
            ],
        )
    except getopt.error as details:
        print(details)
        usage()
    userName = None
    password = None
    perfMonIni = perfMonDll = None
    startup = None
    delayedstart = None
    interactive = None
    waitSecs = 0
    for opt, val in opts:
        if opt == "--username":
            userName = val
        elif opt == "--password":
            password = val
        elif opt == "--perfmonini":
            perfMonIni = val
        elif opt == "--perfmondll":
            perfMonDll = val
        elif opt == "--interactive":
            interactive = 1
        elif opt == "--startup":
            map = {
                "manual": win32service.SERVICE_DEMAND_START,
                "auto": win32service.SERVICE_AUTO_START,
                "delayed": win32service.SERVICE_AUTO_START,  ## ChangeServiceConfig2 called later
                "disabled": win32service.SERVICE_DISABLED,
            }
            startup = map.get(val.lower())
            if not startup:
                print(f"{val!r} is not a valid startup option")
            if val.lower() == "delayed":
                delayedstart = True
            elif val.lower() == "auto":
                delayedstart = False
            # 047668.python.win32serviceutil.line764.comment # else no change
        elif opt == "--wait":
            try:
                waitSecs = int(val)
            except ValueError:
                print("--wait must specify an integer number of seconds.")
                usage()

    arg = args[0]
    knownArg = 0
    # 047669.python.win32serviceutil.line774.comment First we process all arguments which pass additional args on
    if arg == "start":
        knownArg = 1
        print("Starting service %s" % (serviceName))
        try:
            StartService(serviceName, args[1:])
            if waitSecs:
                WaitForServiceStatus(
                    serviceName, win32service.SERVICE_RUNNING, waitSecs
                )
        except win32service.error as exc:
            print("Error starting service: %s" % exc.strerror)
            err = exc.winerror

    elif arg == "restart":
        knownArg = 1
        print("Restarting service %s" % (serviceName))
        RestartService(serviceName, args[1:])
        if waitSecs:
            WaitForServiceStatus(serviceName, win32service.SERVICE_RUNNING, waitSecs)

    elif arg == "debug":
        knownArg = 1
        if not hasattr(sys, "frozen"):
            # 047670.python.win32serviceutil.line798.comment non-frozen services use pythonservice.exe which handles a
            # 047671.python.win32serviceutil.line799.comment -debug option
            svcArgs = " ".join(args[1:])
            try:
                exeName = LocateSpecificServiceExe(serviceName)
            except win32api.error as exc:
                if exc.winerror == winerror.ERROR_FILE_NOT_FOUND:
                    print("The service does not appear to be installed.")
                    print("Please install the service before debugging it.")
                    sys.exit(1)
                raise
            try:
                os.system(f"{exeName} -debug {serviceName} {svcArgs}")
            # 047672.python.win32serviceutil.line811.comment ^C is used to kill the debug service.  Sometimes Python also gets
            # 047673.python.win32serviceutil.line812.comment interrupted - ignore it...
            except KeyboardInterrupt:
                pass
        else:
            # 047674.python.win32serviceutil.line816.comment py2exe services don't use pythonservice - so we simulate
            # 047675.python.win32serviceutil.line817.comment debugging here.
            DebugService(cls, args)

    if not knownArg and len(args) != 1:
        usage()  # the rest of the cmds don't take addn args

    if arg == "install":
        knownArg = 1
        try:
            serviceDeps = cls._svc_deps_
        except AttributeError:
            serviceDeps = None
        try:
            exeName = cls._exe_name_
        except AttributeError:
            exeName = None  # Default to PythonService.exe
        try:
            exeArgs = cls._exe_args_
        except AttributeError:
            exeArgs = None
        try:
            description = cls._svc_description_
        except AttributeError:
            description = None
        print(f"Installing service {serviceName}")
        # 047678.python.win32serviceutil.line842.comment Note that we install the service before calling the custom option
        # 047679.python.win32serviceutil.line843.comment handler, so if the custom handler fails, we have an installed service (from NT's POV)
        # 047680.python.win32serviceutil.line844.comment but is unlikely to work, as the Python code controlling it failed.  Therefore
        # 047681.python.win32serviceutil.line845.comment we remove the service if the first bit works, but the second doesn't!
        try:
            InstallService(
                serviceClassString,
                serviceName,
                serviceDisplayName,
                serviceDeps=serviceDeps,
                startType=startup,
                bRunInteractive=interactive,
                userName=userName,
                password=password,
                exeName=exeName,
                perfMonIni=perfMonIni,
                perfMonDll=perfMonDll,
                exeArgs=exeArgs,
                description=description,
                delayedstart=delayedstart,
            )
            if customOptionHandler:
                customOptionHandler(*(opts,))
            print("Service installed")
        except win32service.error as exc:
            if exc.winerror == winerror.ERROR_SERVICE_EXISTS:
                arg = "update"  # Fall through to the "update" param!
            else:
                print(
                    "Error installing service: %s (%d)" % (exc.strerror, exc.winerror)
                )
                err = exc.winerror
        except ValueError as msg:  # Can be raised by custom option handler.
            print("Error installing service: %s" % str(msg))
            err = -1
            # 047684.python.win32serviceutil.line877.comment xxx - maybe I should remove after _any_ failed install - however,
            # 047685.python.win32serviceutil.line878.comment xxx - it may be useful to help debug to leave the service as it failed.
            # 047686.python.win32serviceutil.line879.comment xxx - We really _must_ remove as per the comments above...
            # 047687.python.win32serviceutil.line880.comment As we failed here, remove the service, so the next installation
            # 047688.python.win32serviceutil.line881.comment attempt works.
            try:
                RemoveService(serviceName)
            except win32api.error:
                print("Warning - could not remove the partially installed service.")

    if arg == "update":
        knownArg = 1
        try:
            serviceDeps = cls._svc_deps_
        except AttributeError:
            serviceDeps = None
        try:
            exeName = cls._exe_name_
        except AttributeError:
            exeName = None  # Default to PythonService.exe
        try:
            exeArgs = cls._exe_args_
        except AttributeError:
            exeArgs = None
        try:
            description = cls._svc_description_
        except AttributeError:
            description = None
        print("Changing service configuration")
        try:
            ChangeServiceConfig(
                serviceClassString,
                serviceName,
                serviceDeps=serviceDeps,
                startType=startup,
                bRunInteractive=interactive,
                userName=userName,
                password=password,
                exeName=exeName,
                displayName=serviceDisplayName,
                perfMonIni=perfMonIni,
                perfMonDll=perfMonDll,
                exeArgs=exeArgs,
                description=description,
                delayedstart=delayedstart,
            )
            if customOptionHandler:
                customOptionHandler(*(opts,))
            print("Service updated")
        except win32service.error as exc:
            print(
                "Error changing service configuration: %s (%d)"
                % (exc.strerror, exc.winerror)
            )
            err = exc.winerror

    elif arg == "remove":
        knownArg = 1
        print("Removing service %s" % (serviceName))
        try:
            RemoveService(serviceName)
            print("Service removed")
        except win32service.error as exc:
            print("Error removing service: %s (%d)" % (exc.strerror, exc.winerror))
            err = exc.winerror
    elif arg == "stop":
        knownArg = 1
        print("Stopping service %s" % (serviceName))
        try:
            if waitSecs:
                StopServiceWithDeps(serviceName, waitSecs=waitSecs)
            else:
                StopService(serviceName)
        except win32service.error as exc:
            print("Error stopping service: %s (%d)" % (exc.strerror, exc.winerror))
            err = exc.winerror
    if not knownArg:
        err = -1
        print("Unknown command - '%s'" % arg)
        usage()
    return err


# 047690.python.win32serviceutil.line960.comment
# 047691.python.win32serviceutil.line961.comment Useful base class to build services from.
# 047692.python.win32serviceutil.line962.comment
class ServiceFramework:
    # 047693.python.win32serviceutil.line964.comment Required Attributes:
    # 047694.python.win32serviceutil.line965.comment _svc_name_ = The service name
    # 047695.python.win32serviceutil.line966.comment _svc_display_name_ = The service display name

    # 047696.python.win32serviceutil.line968.comment Optional Attributes:
    _svc_deps_ = None  # sequence of service names on which this depends
    _exe_name_ = None  # Default to PythonService.exe
    _exe_args_ = None  # Default to no arguments
    _svc_description_ = (
        None  # Only exists on Windows 2000 or later, ignored on windows NT
    )

    def __init__(self, args):
        import servicemanager

        self.ssh = servicemanager.RegisterServiceCtrlHandler(
            args[0], self.ServiceCtrlHandlerEx, True
        )
        servicemanager.SetEventSourceName(self._svc_name_)
        self.checkPoint = 0

    def GetAcceptedControls(self):
        # 047701.python.win32serviceutil.line986.comment Setup the service controls we accept based on our attributes. Note
        # 047702.python.win32serviceutil.line987.comment that if you need to handle controls via SvcOther[Ex](), you must
        # 047703.python.win32serviceutil.line988.comment override this.
        accepted = 0
        if hasattr(self, "SvcStop"):
            accepted |= win32service.SERVICE_ACCEPT_STOP
        if hasattr(self, "SvcPause") and hasattr(self, "SvcContinue"):
            accepted |= win32service.SERVICE_ACCEPT_PAUSE_CONTINUE
        if hasattr(self, "SvcShutdown"):
            accepted |= win32service.SERVICE_ACCEPT_SHUTDOWN
        return accepted

    def ReportServiceStatus(
        self, serviceStatus, waitHint=5000, win32ExitCode=0, svcExitCode=0
    ):
        if self.ssh is None:  # Debugging!
            return
        if serviceStatus == win32service.SERVICE_START_PENDING:
            accepted = 0
        else:
            accepted = self.GetAcceptedControls()

        if serviceStatus in [
            win32service.SERVICE_RUNNING,
            win32service.SERVICE_STOPPED,
        ]:
            checkPoint = 0
        else:
            self.checkPoint += 1
            checkPoint = self.checkPoint

        # 047705.python.win32serviceutil.line1017.comment Now report the status to the control manager
        status = (
            win32service.SERVICE_WIN32_OWN_PROCESS,
            serviceStatus,
            accepted,  # dwControlsAccepted,
            win32ExitCode,  # dwWin32ExitCode;
            svcExitCode,  # dwServiceSpecificExitCode;
            checkPoint,  # dwCheckPoint;
            waitHint,
        )
        win32service.SetServiceStatus(self.ssh, status)

    def SvcInterrogate(self):
        # 047710.python.win32serviceutil.line1030.comment Assume we are running, and everyone is happy.
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

    def SvcOther(self, control):
        try:
            print("Unknown control status - %d" % control)
        except OSError:
            # 047711.python.win32serviceutil.line1037.comment services may not have a valid stdout!
            pass

    def ServiceCtrlHandler(self, control):
        return self.ServiceCtrlHandlerEx(control, 0, None)

    # 047712.python.win32serviceutil.line1043.comment The 'Ex' functions, which take additional params
    def SvcOtherEx(self, control, event_type, data):
        # 047713.python.win32serviceutil.line1045.comment The default here is to call self.SvcOther as that is the old behaviour.
        # 047714.python.win32serviceutil.line1046.comment If you want to take advantage of the extra data, override this method
        return self.SvcOther(control)

    def ServiceCtrlHandlerEx(self, control, event_type, data):
        if control == win32service.SERVICE_CONTROL_STOP:
            return self.SvcStop()
        elif control == win32service.SERVICE_CONTROL_PAUSE:
            return self.SvcPause()
        elif control == win32service.SERVICE_CONTROL_CONTINUE:
            return self.SvcContinue()
        elif control == win32service.SERVICE_CONTROL_INTERROGATE:
            return self.SvcInterrogate()
        elif control == win32service.SERVICE_CONTROL_SHUTDOWN:
            return self.SvcShutdown()
        else:
            return self.SvcOtherEx(control, event_type, data)

    def SvcRun(self):
        # 047715.python.win32serviceutil.line1064.comment This is the entry point the C framework calls when the Service is
        # 047716.python.win32serviceutil.line1065.comment started. Your Service class should implement SvcDoRun().
        # 047717.python.win32serviceutil.line1066.comment Or you can override this method for more control over the Service
        # 047718.python.win32serviceutil.line1067.comment statuses reported to the SCM.

        # 047719.python.win32serviceutil.line1069.comment If this method raises an exception, the C framework will detect this
        # 047720.python.win32serviceutil.line1070.comment and report a SERVICE_STOPPED status with a non-zero error code.

        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.SvcDoRun()
        # 047721.python.win32serviceutil.line1074.comment Once SvcDoRun terminates, the service has stopped.
        # 047722.python.win32serviceutil.line1075.comment We tell the SCM the service is still stopping - the C framework
        # 047723.python.win32serviceutil.line1076.comment will automatically tell the SCM it has stopped when this returns.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
