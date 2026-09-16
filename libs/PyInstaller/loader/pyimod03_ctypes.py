# 009512.python.pyimod03_ctypes.line1.comment -----------------------------------------------------------------------------
# 009513.python.pyimod03_ctypes.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 009514.python.pyimod03_ctypes.line3.comment
# 009515.python.pyimod03_ctypes.line4.comment Distributed under the terms of the GNU General Public License with exception
# 009516.python.pyimod03_ctypes.line5.comment for distributing bootloader.
# 009517.python.pyimod03_ctypes.line6.comment
# 009518.python.pyimod03_ctypes.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009519.python.pyimod03_ctypes.line8.comment -----------------------------------------------------------------------------
"""
Hooks to make ctypes.CDLL, .PyDLL, etc. look in sys._MEIPASS first.
"""

import sys


def install():
    """
    Install the hooks.

    This must be done from a function as opposed to at module-level, because when the module is imported/executed,
    the import machinery is not completely set up yet.
    """

    import os

    try:
        import ctypes
    except ImportError:
        # 009520.python.pyimod03_ctypes.line29.comment ctypes is not included in the frozen application
        return

    def _frozen_name(name):
        # 009521.python.pyimod03_ctypes.line33.comment If the given (file)name does not exist, fall back to searching for its basename in sys._MEIPASS, where
        # 009522.python.pyimod03_ctypes.line34.comment PyInstaller usually collects shared libraries.
        if name and not os.path.isfile(name):
            frozen_name = os.path.join(sys._MEIPASS, os.path.basename(name))
            if os.path.isfile(frozen_name):
                name = frozen_name
        return name

    class PyInstallerImportError(OSError):
        def __init__(self, name):
            self.msg = (
                "Failed to load dynlib/dll %r. Most likely this dynlib/dll was not found when the application "
                "was frozen." % name
            )
            self.args = (self.msg,)

    class PyInstallerCDLL(ctypes.CDLL):
        def __init__(self, name, *args, **kwargs):
            name = _frozen_name(name)
            try:
                super().__init__(name, *args, **kwargs)
            except Exception as base_error:
                raise PyInstallerImportError(name) from base_error

    ctypes.CDLL = PyInstallerCDLL
    ctypes.cdll = ctypes.LibraryLoader(PyInstallerCDLL)

    class PyInstallerPyDLL(ctypes.PyDLL):
        def __init__(self, name, *args, **kwargs):
            name = _frozen_name(name)
            try:
                super().__init__(name, *args, **kwargs)
            except Exception as base_error:
                raise PyInstallerImportError(name) from base_error

    ctypes.PyDLL = PyInstallerPyDLL
    ctypes.pydll = ctypes.LibraryLoader(PyInstallerPyDLL)

    if sys.platform.startswith('win'):

        class PyInstallerWinDLL(ctypes.WinDLL):
            def __init__(self, name, *args, **kwargs):
                name = _frozen_name(name)
                try:
                    super().__init__(name, *args, **kwargs)
                except Exception as base_error:
                    raise PyInstallerImportError(name) from base_error

        ctypes.WinDLL = PyInstallerWinDLL
        ctypes.windll = ctypes.LibraryLoader(PyInstallerWinDLL)

        class PyInstallerOleDLL(ctypes.OleDLL):
            def __init__(self, name, *args, **kwargs):
                name = _frozen_name(name)
                try:
                    super().__init__(name, *args, **kwargs)
                except Exception as base_error:
                    raise PyInstallerImportError(name) from base_error

        ctypes.OleDLL = PyInstallerOleDLL
        ctypes.oledll = ctypes.LibraryLoader(PyInstallerOleDLL)

        try:
            import ctypes.util
        except ImportError:
            # 009523.python.pyimod03_ctypes.line98.comment ctypes.util is not included in the frozen application
            return

        # 009524.python.pyimod03_ctypes.line101.comment Same implementation as ctypes.util.find_library, except it prepends sys._MEIPASS to the search directories.
        def pyinstaller_find_library(name):
            if name in ('c', 'm'):
                return ctypes.util.find_msvcrt()
            # 009525.python.pyimod03_ctypes.line105.comment See MSDN for the REAL search order.
            search_dirs = [sys._MEIPASS] + os.environ['PATH'].split(os.pathsep)
            for directory in search_dirs:
                fname = os.path.join(directory, name)
                if os.path.isfile(fname):
                    return fname
                if fname.lower().endswith(".dll"):
                    continue
                fname = fname + ".dll"
                if os.path.isfile(fname):
                    return fname
            return None

        ctypes.util.find_library = pyinstaller_find_library


# 009526.python.pyimod03_ctypes.line121.comment On macOS insert sys._MEIPASS in the first position of the list of paths that ctypes uses to search for libraries.
# 009527.python.pyimod03_ctypes.line122.comment
# 009528.python.pyimod03_ctypes.line123.comment Note: 'ctypes' module will NOT be bundled with every app because code in this module is not scanned for module
# 009529.python.pyimod03_ctypes.line124.comment dependencies. It is safe to wrap 'ctypes' module into 'try/except ImportError' block.
if sys.platform.startswith('darwin'):
    try:
        from ctypes.macholib import dyld
        dyld.DEFAULT_LIBRARY_FALLBACK.insert(0, sys._MEIPASS)
    except ImportError:
        # 009530.python.pyimod03_ctypes.line130.comment Do nothing when module 'ctypes' is not available.
        pass
