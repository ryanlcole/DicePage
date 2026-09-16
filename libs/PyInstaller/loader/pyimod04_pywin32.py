# 009531.python.pyimod04_pywin32.line1.comment -----------------------------------------------------------------------------
# 009532.python.pyimod04_pywin32.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 009533.python.pyimod04_pywin32.line3.comment
# 009534.python.pyimod04_pywin32.line4.comment Distributed under the terms of the GNU General Public License with exception
# 009535.python.pyimod04_pywin32.line5.comment for distributing bootloader.
# 009536.python.pyimod04_pywin32.line6.comment
# 009537.python.pyimod04_pywin32.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009538.python.pyimod04_pywin32.line8.comment -----------------------------------------------------------------------------
"""
Set search path for pywin32 DLLs. Due to the large number of pywin32 modules, we use a single loader-level script
instead of per-module runtime hook scripts.
"""

import os
import sys


def install():
    # 009539.python.pyimod04_pywin32.line19.comment Sub-directories containing extensions. In original python environment, these are added to `sys.path` by the
    # 009540.python.pyimod04_pywin32.line20.comment `pywin32.pth` so the extensions end up treated as top-level modules. We attempt to preserve the directory
    # 009541.python.pyimod04_pywin32.line21.comment layout, so we need to add these directories to `sys.path` ourselves.
    pywin32_ext_paths = ('win32', 'pythonwin')
    pywin32_ext_paths = [os.path.join(sys._MEIPASS, pywin32_ext_path) for pywin32_ext_path in pywin32_ext_paths]
    pywin32_ext_paths = [path for path in pywin32_ext_paths if os.path.isdir(path)]
    sys.path.extend(pywin32_ext_paths)

    # 009542.python.pyimod04_pywin32.line27.comment Additional handling of `pywin32_system32` DLL directory
    pywin32_system32_path = os.path.join(sys._MEIPASS, 'pywin32_system32')

    if not os.path.isdir(pywin32_system32_path):
        # 009543.python.pyimod04_pywin32.line31.comment Either pywin32 is not collected, or we are dealing with version that does not use the pywin32_system32
        # 009544.python.pyimod04_pywin32.line32.comment sub-directory. In the latter case, the pywin32 DLLs should be in `sys._MEIPASS`, and nothing
        # 009545.python.pyimod04_pywin32.line33.comment else needs to be done here.
        return

    # 009546.python.pyimod04_pywin32.line36.comment Add the DLL directory to `sys.path`.
    # 009547.python.pyimod04_pywin32.line37.comment This is necessary because `__import_pywin32_system_module__` from `pywintypes` module assumes that in a frozen
    # 009548.python.pyimod04_pywin32.line38.comment application, the pywin32 DLLs (`pythoncom3X.dll` and `pywintypes3X.dll`) that are normally found in
    # 009549.python.pyimod04_pywin32.line39.comment `pywin32_system32` sub-directory in `sys.path` (site-packages, really) are located directly in `sys.path`.
    # 009550.python.pyimod04_pywin32.line40.comment This obviously runs afoul of our attempts at preserving the directory layout and placing them in the
    # 009551.python.pyimod04_pywin32.line41.comment `pywin32_system32` sub-directory instead of the top-level application directory.
    sys.path.append(pywin32_system32_path)

    # 009552.python.pyimod04_pywin32.line44.comment Add the DLL directory to DLL search path using os.add_dll_directory().
    # 009553.python.pyimod04_pywin32.line45.comment This allows extensions from win32 directory (e.g., win32api, win32crypt) to be loaded on their own without
    # 009554.python.pyimod04_pywin32.line46.comment importing pywintypes first. The extensions are linked against pywintypes3X.dll.
    os.add_dll_directory(pywin32_system32_path)

    # 009555.python.pyimod04_pywin32.line49.comment Add the DLL directory to PATH. This is necessary under certain versions of
    # 009556.python.pyimod04_pywin32.line50.comment Anaconda python, where `os.add_dll_directory` does not work.
    path = os.environ.get('PATH', None)
    if not path:
        path = pywin32_system32_path
    else:
        path = pywin32_system32_path + os.pathsep + path
    os.environ['PATH'] = path
