# 038020.python.startup.line1.comment startup.py
# 038021.python.startup.line2.comment
"The main application startup code for PythonWin."

# 038022.python.startup.line5.comment
# 038023.python.startup.line6.comment This does the basic command line handling.

# 038024.python.startup.line8.comment Keep this as short as possible, cos error output is only redirected if
# 038025.python.startup.line9.comment this runs OK.  Errors in imported modules are much better - the messages go somewhere (not any more :-)

import os
import sys

import win32api
import win32ui

if not sys.argv:
    # 038026.python.startup.line18.comment Initialize sys.argv from commandline. When sys.argv is empty list (
    # 038027.python.startup.line19.comment different from [''] meaning "no cmd line arguments" ), then C
    # 038028.python.startup.line20.comment bootstrapping or another method of invocation failed to initialize
    # 038029.python.startup.line21.comment sys.argv and it will be done here. ( This was a workaround for a bug in
    # 038030.python.startup.line22.comment win32ui but is retained for other situations. )
    argv = win32api.CommandLineToArgv(win32api.GetCommandLine())
    sys.argv = argv[1:]
    if os.getcwd() not in sys.path and "." not in sys.path:
        sys.path.insert(0, os.getcwd())

# 038031.python.startup.line28.comment You may wish to redirect error output somewhere useful if you have startup errors.
# 038032.python.startup.line29.comment eg, 'import win32traceutil' will do this for you.
# 038033.python.startup.line30.comment import win32traceutil # Just uncomment this line to see error output!

# 038034.python.startup.line32.comment An old class I used to use - generally only useful if Pythonwin is running under MSVC
# 038035.python.startup.line33.comment class DebugOutput:
# 038036.python.startup.line34.comment softspace=1
# 038037.python.startup.line35.comment def write(self,message):
# 038038.python.startup.line36.comment win32ui.OutputDebug(message)
# 038039.python.startup.line37.comment sys.stderr=sys.stdout=DebugOutput()

# 038040.python.startup.line39.comment To fix a problem with Pythonwin when started from the Pythonwin directory,
# 038041.python.startup.line40.comment we update the pywin path to ensure it is absolute.
# 038042.python.startup.line41.comment If it is indeed relative, it will be relative to our current directory.
# 038043.python.startup.line42.comment If it's already absolute, then this will have no affect.
import pywin
import pywin.framework

# 038044.python.startup.line46.comment Ensure we're working on __path__ as list, not Iterable
pywin.__path__ = list(pywin.__path__)
pywin.framework.__path__ = list(pywin.framework.__path__)

pywin.__path__[0] = win32ui.FullPath(pywin.__path__[0])
pywin.framework.__path__[0] = win32ui.FullPath(pywin.framework.__path__[0])

# 038045.python.startup.line53.comment make a few weird sys values.  This is so later we can clobber sys.argv to trick
# 038046.python.startup.line54.comment scripts when running under a GUI environment.

moduleName = "pywin.framework.intpyapp"
sys.appargvoffset = 0
sys.appargv = sys.argv[:]
# 038047.python.startup.line59.comment Must check for /app param here.
if len(sys.argv) >= 2 and sys.argv[0].lower() in ("/app", "-app"):
    from . import cmdline

    moduleName = cmdline.FixArgFileName(sys.argv[1])
    sys.appargvoffset = 2
    newargv = sys.argv[sys.appargvoffset :]
    # 038048.python.startup.line66.comment newargv.insert(0, sys.argv[0])
    sys.argv = newargv

# 038049.python.startup.line69.comment Import the application module.
__import__(moduleName)
