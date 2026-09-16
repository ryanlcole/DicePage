# 018267.python.hook-usb.line1.comment ------------------------------------------------------------------
# 018268.python.hook-usb.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018269.python.hook-usb.line3.comment
# 018270.python.hook-usb.line4.comment This file is distributed under the terms of the GNU General Public
# 018271.python.hook-usb.line5.comment License (version 2.0 or later).
# 018272.python.hook-usb.line6.comment
# 018273.python.hook-usb.line7.comment The full license is available in LICENSE, distributed with
# 018274.python.hook-usb.line8.comment this software.
# 018275.python.hook-usb.line9.comment
# 018276.python.hook-usb.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018277.python.hook-usb.line11.comment ------------------------------------------------------------------

import ctypes.util
import os

from PyInstaller.depend.utils import _resolveCtypesImports
from PyInstaller.compat import is_cygwin, getenv
from PyInstaller.utils.hooks import logger

# 018278.python.hook-usb.line20.comment Include glob for library lookup in run-time hook.
hiddenimports = ['glob']

# 018279.python.hook-usb.line23.comment https://github.com/walac/pyusb/blob/master/docs/faq.rst
# 018280.python.hook-usb.line24.comment https://github.com/walac/pyusb/blob/master/docs/tutorial.rst

binaries = []

# 018281.python.hook-usb.line28.comment Running usb.core.find() in this script crashes Ubuntu 14.04LTS,
# 018282.python.hook-usb.line29.comment let users circumvent pyusb discovery with an environment variable.
skip_pyusb_discovery = \
    bool(getenv('PYINSTALLER_USB_HOOK_SKIP_PYUSB_DISCOVERY'))

# 018283.python.hook-usb.line33.comment Try to use pyusb's library locator.
if not skip_pyusb_discovery:
    import usb.core
    import usb.backend
    try:
        # 018284.python.hook-usb.line38.comment get the backend symbols before find
        backend_contents_before_discovery = set(dir(usb.backend))
        # 018285.python.hook-usb.line40.comment perform find, which will load a usb library if found
        usb.core.find()
        # 018286.python.hook-usb.line42.comment get the backend symbols which have been added (loaded)
        backends = set(dir(usb.backend)) - backend_contents_before_discovery
        for usblib in [getattr(usb.backend, be)._lib for be in backends]:
            if usblib is not None:
                if os.path.isabs(usblib._name):
                    binaries.append((os.path.basename(usblib._name), usblib._name, "BINARY"))
                else:
                    # 018287.python.hook-usb.line49.comment OSX returns the full path, Linux only the filename.
                    # 018288.python.hook-usb.line50.comment try to resolve the library names to absolute paths.
                    backend_lib_full_paths = _resolveCtypesImports([os.path.basename(usblib._name)])
                    if backend_lib_full_paths:
                        binaries.append(backend_lib_full_paths[0])
    except (ValueError, usb.core.USBError) as exc:
        logger.warning("%s", exc)

# 018289.python.hook-usb.line57.comment If pyusb didn't find a backend, manually search for usb libraries.
if not binaries:
    # 018290.python.hook-usb.line59.comment NOTE: Update these lists when adding further libs.
    if is_cygwin:
        libusb_candidates = ['cygusb-1.0-0.dll', 'cygusb0.dll']
    else:
        libusb_candidates = [
            # 018291.python.hook-usb.line64.comment libusb10
            'usb-1.0',
            'usb',
            'libusb-1.0',
            # 018292.python.hook-usb.line68.comment libusb01
            'usb-0.1',
            'libusb0',
            # 018293.python.hook-usb.line71.comment openusb
            'openusb',
        ]

    backend_library_basenames = []
    for candidate in libusb_candidates:
        libname = ctypes.util.find_library(candidate)
        if libname is not None:
            if os.path.isabs(libname):
                binaries.append((os.path.basename(libname), libname, "BINARY"))
            else:
                backend_lib_full_paths = _resolveCtypesImports([os.path.basename(libname)])
                if backend_lib_full_paths:
                    binaries.append(backend_lib_full_paths[0])

# 018294.python.hook-usb.line86.comment Validate and normalize the first found usb library.
if binaries:
    # 018295.python.hook-usb.line88.comment `_resolveCtypesImports` returns a 3-tuple, but `binaries` are only
    # 018296.python.hook-usb.line89.comment 2-tuples, so remove the last element:
    assert len(binaries[0]) == 3
    binaries = [(binaries[0][1], '.')]
