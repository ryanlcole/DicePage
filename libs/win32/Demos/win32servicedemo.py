import win32con
import win32service


def EnumServices():
    resume = 0
    accessSCM = win32con.GENERIC_READ
    accessSrv = win32service.SC_MANAGER_ALL_ACCESS

    # 046644.python.win32servicedemo.line10.comment Open Service Control Manager
    hscm = win32service.OpenSCManager(None, None, accessSCM)

    # 046645.python.win32servicedemo.line13.comment Enumerate Service Control Manager DB

    typeFilter = win32service.SERVICE_WIN32
    stateFilter = win32service.SERVICE_STATE_ALL

    statuses = win32service.EnumServicesStatus(hscm, typeFilter, stateFilter)
    for short_name, desc, status in statuses:
        print(short_name, desc, status)


EnumServices()
