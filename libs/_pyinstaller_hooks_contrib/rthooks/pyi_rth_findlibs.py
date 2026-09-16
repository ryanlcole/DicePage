# 011530.python.pyi_rth_findlibs.line1.comment -----------------------------------------------------------------------------
# 011531.python.pyi_rth_findlibs.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 011532.python.pyi_rth_findlibs.line3.comment
# 011533.python.pyi_rth_findlibs.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 011534.python.pyi_rth_findlibs.line5.comment you may not use this file except in compliance with the License.
# 011535.python.pyi_rth_findlibs.line6.comment
# 011536.python.pyi_rth_findlibs.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 011537.python.pyi_rth_findlibs.line8.comment
# 011538.python.pyi_rth_findlibs.line9.comment SPDX-License-Identifier: Apache-2.0
# 011539.python.pyi_rth_findlibs.line10.comment -----------------------------------------------------------------------------

# 011540.python.pyi_rth_findlibs.line12.comment Override the findlibs.find() function to give precedence to sys._MEIPASS, followed by `ctypes.util.find_library`,
# 011541.python.pyi_rth_findlibs.line13.comment and only then the hard-coded paths from the original implementation. The main aim here is to avoid loading libraries
# 011542.python.pyi_rth_findlibs.line14.comment from Homebrew environment on macOS when it happens to be present at run-time and we have a bundled copy collected from
# 011543.python.pyi_rth_findlibs.line15.comment the build system. This happens because we (try not to) modify `DYLD_LIBRARY_PATH`, and the original `findlibs.find()`
# 011544.python.pyi_rth_findlibs.line16.comment implementation gives precedence to environment variables and several fixed/hard-coded locations, and uses
# 011545.python.pyi_rth_findlibs.line17.comment `ctypes.util.find_library` as the final fallback...
def _pyi_rthook():
    import sys
    import os
    import ctypes.util

    # 011546.python.pyi_rth_findlibs.line23.comment findlibs v0.1.0 broke compatibility with python < 3.10; due to incompatible typing annotation, attempting to
    # 011547.python.pyi_rth_findlibs.line24.comment import the package raises `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`. Gracefully
    # 011548.python.pyi_rth_findlibs.line25.comment handle this situation by making this run-time hook no-op, in order to avoid crashing the frozen program even
    # 011549.python.pyi_rth_findlibs.line26.comment if it would never end up importing/using `findlibs`.
    try:
        import findlibs
    except TypeError:
        return

    _orig_find = getattr(findlibs, 'find', None)

    def _pyi_find(lib_name, *args, **kwargs):
        extension = findlibs.EXTENSIONS.get(sys.platform, ".so")

        # 011550.python.pyi_rth_findlibs.line37.comment First check sys._MEIPASS
        fullname = os.path.join(sys._MEIPASS, "lib{}{}".format(lib_name, extension))
        if os.path.isfile(fullname):
            return fullname

        # 011551.python.pyi_rth_findlibs.line42.comment Fall back to `ctypes.util.find_library` (to give it precedence over hard-coded paths from original
        # 011552.python.pyi_rth_findlibs.line43.comment implementation).
        lib = ctypes.util.find_library(lib_name)
        if lib is not None:
            return lib

        # 011553.python.pyi_rth_findlibs.line48.comment Finally, fall back to original implementation
        if _orig_find is not None:
            return _orig_find(lib_name, *args, **kwargs)

        return None

    findlibs.find = _pyi_find


_pyi_rthook()
del _pyi_rthook
