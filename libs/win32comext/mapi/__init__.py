if isinstance(__path__, str):
    # 051432.python.init.line2.comment For freeze to work!
    import sys

    try:
        import mapi

        sys.modules["win32com.mapi.mapi"] = mapi
    except ImportError:
        pass
    try:
        import exchange

        sys.modules["win32com.mapi.exchange"] = exchange
    except ImportError:
        pass
else:
    import win32com

    # 051433.python.init.line20.comment See if we have a special directory for the binaries (for developers)
    win32com.__PackageSupportBuildPath__(__path__)
