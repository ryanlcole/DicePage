# 037095.python.fail.line1.comment NOTE NOTE - This module is designed to fail!
# 037096.python.fail.line2.comment
# 037097.python.fail.line3.comment The ONLY purpose for this script is testing/demoing the
# 037098.python.fail.line4.comment Pythonwin debugger package.

# 037099.python.fail.line6.comment It does nothing useful, and it even doesn't do that!

import sys
import time

import pywin.debugger


def a():
    a = 1
    try:
        b()
    except:
        # 037100.python.fail.line19.comment Break into the debugger with the exception information.
        pywin.debugger.post_mortem(sys.exc_info()[2])
        a = 1
        a = 2
        a = 3
        a = 4


def b():
    b = 1
    pywin.debugger.set_trace()
    # 037101.python.fail.line30.comment After importing or running this module, you are likely to be
    # 037102.python.fail.line31.comment sitting at the next line.  This is because we explicitly
    # 037103.python.fail.line32.comment broke into the debugger using the "set_trace() function
    # 037104.python.fail.line33.comment "pywin.debugger.brk()" is a shorter alias for this.
    c()


def c():
    c = 1
    d()


def d():
    d = 1
    e(d)
    raise ValueError("Hi")


def e(arg):
    e = 1
    time.sleep(1)
    return e


a()
