# 008595.python.child.line1.comment -----------------------------------------------------------------------------
# 008596.python.child.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 008597.python.child.line3.comment
# 008598.python.child.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 008599.python.child.line5.comment or later) or, at the user's discretion, the MIT License.
# 008600.python.child.line6.comment
# 008601.python.child.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008602.python.child.line8.comment
# 008603.python.child.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception OR MIT)
# 008604.python.child.line10.comment -----------------------------------------------------------------------------
"""
The child process to be invoked by IsolatedPython().

This file is to be run directly with pipe handles for reading from and writing to the parent process as command line
arguments.

"""

import sys
import os
import types
from marshal import loads, dumps
from base64 import b64encode, b64decode
from traceback import format_exception

if os.name == "nt":
    from msvcrt import open_osfhandle

    def _open(osf_handle, mode):
        # 008605.python.child.line30.comment Convert system file handles to file descriptors before opening them.
        return open(open_osfhandle(osf_handle, 0), mode)
else:
    _open = open


def run_next_command(read_fh, write_fh):
    """
    Listen to **read_fh** for the next function to run. Write the result to **write_fh**.
    """

    # 008606.python.child.line41.comment Check the first line of input. Receiving an empty line is the signal that there are no more tasks to be ran.
    first_line = read_fh.readline()
    if first_line == b"\n":
        # 008607.python.child.line44.comment It's time to end this child process
        return False

    # 008608.python.child.line47.comment There are 5 lines to read: The function's code, its default args, its default kwargs, its args, and its kwargs.
    code = loads(b64decode(first_line.strip()))
    _defaults = loads(b64decode(read_fh.readline().strip()))
    _kwdefaults = loads(b64decode(read_fh.readline().strip()))
    args = loads(b64decode(read_fh.readline().strip()))
    kwargs = loads(b64decode(read_fh.readline().strip()))

    try:
        # 008609.python.child.line55.comment Define the global namespace available to the function.
        GLOBALS = {"__builtins__": __builtins__, "__isolated__": True}
        # 008610.python.child.line57.comment Reconstruct the function.
        function = types.FunctionType(code, GLOBALS)
        function.__defaults__ = _defaults
        function.__kwdefaults__ = _kwdefaults

        # 008611.python.child.line62.comment Run it.
        output = function(*args, **kwargs)

        # 008612.python.child.line65.comment Verify that the output is serialise-able (i.e. no custom types or module or function references) here so that
        # 008613.python.child.line66.comment it's caught if it fails.
        marshalled = dumps((True, output))

    except BaseException as ex:
        # 008614.python.child.line70.comment An exception happened whilst either running the function or serialising its output. Send back a string
        # 008615.python.child.line71.comment version of the traceback (unfortunately raw traceback objects are not marshal-able) and a boolean to say
        # 008616.python.child.line72.comment that it failed.
        tb_lines = format_exception(type(ex), ex, ex.__traceback__)
        if tb_lines[0] == "Traceback (most recent call last):\n":
            # 008617.python.child.line75.comment This particular line is distracting. Get rid of it.
            tb_lines = tb_lines[1:]
        marshalled = dumps((False, "".join(tb_lines).rstrip()))

    # 008618.python.child.line79.comment Send the output (return value or traceback) back to the parent.
    write_fh.write(b64encode(marshalled))
    write_fh.write(b"\n")
    write_fh.flush()

    # 008619.python.child.line84.comment Signal that an instruction was ran (successfully or otherwise).
    return True


if __name__ == '__main__':
    # 008620.python.child.line89.comment Mark this process as PyInstaller's isolated subprocess; this makes attempts at spawning further isolated
    # 008621.python.child.line90.comment subprocesses via `PyInstaller.isolated` from this process no-op.
    sys._pyi_isolated_subprocess = True

    read_from_parent, write_to_parent = map(int, sys.argv[1:])

    with _open(read_from_parent, "rb") as read_fh:
        with _open(write_to_parent, "wb") as write_fh:
            sys.path = loads(b64decode(read_fh.readline()))

            # 008622.python.child.line99.comment Keep receiving and running instructions until the parent sends the signal to stop.
            while run_next_command(read_fh, write_fh):
                pass
