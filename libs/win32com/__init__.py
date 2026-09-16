# 048544.python.init.line1.comment
# 048545.python.init.line2.comment Initialization for the win32com package
# 048546.python.init.line3.comment
from __future__ import annotations

import os
import sys

import pythoncom
import win32api

# 048547.python.init.line12.comment flag if we are in a "frozen" build.
_frozen = getattr(sys, "frozen", False)
# 048548.python.init.line14.comment pythoncom dumbly defaults this to zero - we believe sys.frozen over it.
if _frozen and not getattr(pythoncom, "frozen", 0):
    pythoncom.frozen = sys.frozen

# 048549.python.init.line18.comment Add support for an external "COM Extensions" path.
# 048550.python.init.line19.comment Concept is that you can register a seperate path to be used for
# 048551.python.init.line20.comment COM extensions, outside of the win32com directory.  These modules, however,
# 048552.python.init.line21.comment look identical to win32com built-in modules.
# 048553.python.init.line22.comment This is the technique that we use for the "standard" COM extensions.
# 048554.python.init.line23.comment eg "win32com.mapi" or "win32com.axscript" both work, even though they do not
# 048555.python.init.line24.comment live under the main win32com directory.
__gen_path__ = ""
__build_path__ = None
# 048556.python.init.line27.comment ## TODO - Load _all_ \\Extensions subkeys - for now, we only read the default
# 048557.python.init.line28.comment ## Modules will work if loaded into "win32comext" path.

# 048558.python.init.line30.comment Ensure we're working on __path__ as list, not Iterable
__path__: list[str] = list(__path__)  # type: ignore[no-redef]


def SetupEnvironment():
    HKEY_LOCAL_MACHINE = -2147483646  # Avoid pulling in win32con for just these...
    KEY_QUERY_VALUE = 0x1
    # 048561.python.init.line37.comment Open the root key once, as this is quite slow on NT.
    try:
        keyName = "SOFTWARE\\Python\\PythonCore\\%s\\PythonPath\\win32com" % sys.winver
        key = win32api.RegOpenKey(HKEY_LOCAL_MACHINE, keyName, 0, KEY_QUERY_VALUE)
    except (win32api.error, AttributeError):
        key = None

    try:
        found = 0
        if key is not None:
            try:
                __path__.append(win32api.RegQueryValue(key, "Extensions"))
                found = 1
            except win32api.error:
                # 048562.python.init.line51.comment Nothing registered
                pass
        if not found:
            try:
                __path__.append(
                    win32api.GetFullPathName(__path__[0] + "\\..\\win32comext")
                )
            except win32api.error:
                # 048563.python.init.line59.comment Give up in disgust!
                pass

        # 048564.python.init.line62.comment For the sake of developers, we also look up a "BuildPath" key
        # 048565.python.init.line63.comment If extension modules add support, we can load their .pyd's from a completely
        # 048566.python.init.line64.comment different directory (see the comments below)
        try:
            if key is not None:
                global __build_path__
                __build_path__ = win32api.RegQueryValue(key, "BuildPath")
                __path__.append(__build_path__)
        except win32api.error:
            # 048567.python.init.line71.comment __build_path__ neednt be defined.
            pass
        global __gen_path__
        if key is not None:
            try:
                __gen_path__ = win32api.RegQueryValue(key, "GenPath")
            except win32api.error:
                pass
    finally:
        if key is not None:
            key.Close()


# 048568.python.init.line84.comment A Helper for developers.  A sub-package's __init__ can call this help function,
# 048569.python.init.line85.comment which allows the .pyd files for the extension to live in a special "Build" directory
# 048570.python.init.line86.comment (which the win32com developers do!)
def __PackageSupportBuildPath__(package_path):
    # 048571.python.init.line88.comment See if we have a special directory for the binaries (for developers)
    if not _frozen and __build_path__:
        package_path.append(__build_path__)


if not _frozen:
    SetupEnvironment()

# 048572.python.init.line96.comment If we don't have a special __gen_path__, see if we have a gen_py as a
# 048573.python.init.line97.comment normal module and use that (ie, "win32com.gen_py" may already exist as
# 048574.python.init.line98.comment a package.
if not __gen_path__:
    try:
        import win32com.gen_py

        # 048575.python.init.line103.comment __path__ is only ensured to be an Iterable, not a list.
        __gen_path__ = next(iter(sys.modules["win32com.gen_py"].__path__))
    except ImportError:
        # 048576.python.init.line106.comment If a win32com\gen_py directory already exists, then we use it
        # 048577.python.init.line107.comment (gencache doesn't insist it have an __init__, but our __import__
        # 048578.python.init.line108.comment above does!
        __gen_path__ = os.path.abspath(os.path.join(__path__[0], "gen_py"))
        if not os.path.isdir(__gen_path__):
            # 048579.python.init.line111.comment We used to dynamically create a directory under win32com -
            # 048580.python.init.line112.comment but this sucks.  If the dir doesn't already exist, we
            # 048581.python.init.line113.comment create a version specific directory under the user temp
            # 048582.python.init.line114.comment directory.
            __gen_path__ = os.path.join(
                win32api.GetTempPath(),
                "gen_py",
                "%d.%d" % (sys.version_info.major, sys.version_info.minor),
            )

# 048583.python.init.line121.comment we must have a __gen_path__, but may not have a gen_py module -
# 048584.python.init.line122.comment set that up.
if "win32com.gen_py" not in sys.modules:
    # 048585.python.init.line124.comment Create a "win32com.gen_py", but with a custom __path__
    import types

    gen_py = types.ModuleType("win32com.gen_py")
    gen_py.__path__ = [__gen_path__]
    sys.modules[gen_py.__name__] = gen_py
    del types
gen_py = sys.modules["win32com.gen_py"]

# 048586.python.init.line133.comment get rid of these for module users
del os, sys, win32api, pythoncom
