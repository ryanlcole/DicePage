# 011696.python.pyi_rth_usb.line1.comment -----------------------------------------------------------------------------
# 011697.python.pyi_rth_usb.line2.comment Copyright (c) 2013-2020, PyInstaller Development Team.
# 011698.python.pyi_rth_usb.line3.comment
# 011699.python.pyi_rth_usb.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011700.python.pyi_rth_usb.line5.comment
# 011701.python.pyi_rth_usb.line6.comment The full license is available in LICENSE, distributed with
# 011702.python.pyi_rth_usb.line7.comment this software.
# 011703.python.pyi_rth_usb.line8.comment
# 011704.python.pyi_rth_usb.line9.comment SPDX-License-Identifier: Apache-2.0
# 011705.python.pyi_rth_usb.line10.comment -----------------------------------------------------------------------------


import ctypes
import glob
import os
import sys
# 011706.python.pyi_rth_usb.line17.comment Pyusb changed these libusb module names in commit 2082e7.
try:
    import usb.backend.libusb10 as libusb10
except ImportError:
    import usb.backend.libusb1 as libusb10
try:
    import usb.backend.libusb01 as libusb01
except ImportError:
    import usb.backend.libusb0 as libusb01
import usb.backend.openusb as openusb


def get_load_func(type, candidates):

    def _load_library(find_library=None):
        exec_path = sys._MEIPASS

        library = None
        for candidate in candidates:

            # 011707.python.pyi_rth_usb.line37.comment Find a list of library files that match 'candidate'.
            if find_library:
                # 011708.python.pyi_rth_usb.line39.comment Caller provides a function that lookup lib path by candidate name.
                lib_path = find_library(candidate)
                libs = [lib_path] if lib_path else []
            else:
                # 011709.python.pyi_rth_usb.line43.comment No find_library callback function, we look at the default location.
                if os.name == 'posix' and sys.platform == 'darwin':
                    libs = glob.glob("%s/%s*.dylib*" % (exec_path, candidate))
                elif sys.platform == 'win32' or sys.platform == 'cygwin':
                    libs = glob.glob("%s\\%s*.dll" % (exec_path, candidate))
                else:
                    libs = glob.glob("%s/%s*.so*" % (exec_path, candidate))

            # 011710.python.pyi_rth_usb.line51.comment Do linker's path lookup work to force load bundled copy.
            for libname in libs:
                try:
                    # 011711.python.pyi_rth_usb.line54.comment NOTE: libusb01 is using CDLL under win32.
                    # 011712.python.pyi_rth_usb.line55.comment (see usb.backends.libusb01)
                    if sys.platform == 'win32' and type != 'libusb01':
                        library = ctypes.WinDLL(libname)
                    else:
                        library = ctypes.CDLL(libname)
                    if library is not None:
                        break
                except OSError:
                    library = None
            if library is not None:
                break
        else:
            raise OSError('USB library could not be found')

        if type == 'libusb10':
            if not hasattr(library, 'libusb_init'):
                raise OSError('USB library could not be found')
        return library

    return _load_library


# 011713.python.pyi_rth_usb.line77.comment NOTE: Need to keep in sync with future PyUSB updates.
if sys.platform == 'cygwin':
    libusb10._load_library = get_load_func('libusb10', ('cygusb-1.0', ))
    libusb01._load_library = get_load_func('libusb01', ('cygusb0', ))
    openusb._load_library = get_load_func('openusb', ('openusb', ))
else:
    libusb10._load_library = get_load_func('libusb10', ('usb-1.0', 'libusb-1.0', 'usb'))
    libusb01._load_library = get_load_func('libusb01', ('usb-0.1', 'usb', 'libusb0', 'libusb'))
    openusb._load_library = get_load_func('openusb', ('openusb', ))
