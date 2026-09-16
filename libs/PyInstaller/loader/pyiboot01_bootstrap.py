# 009262.python.pyiboot01_bootstrap.line1.comment -----------------------------------------------------------------------------
# 009263.python.pyiboot01_bootstrap.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 009264.python.pyiboot01_bootstrap.line3.comment
# 009265.python.pyiboot01_bootstrap.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 009266.python.pyiboot01_bootstrap.line5.comment or later) with exception for distributing the bootloader.
# 009267.python.pyiboot01_bootstrap.line6.comment
# 009268.python.pyiboot01_bootstrap.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009269.python.pyiboot01_bootstrap.line8.comment
# 009270.python.pyiboot01_bootstrap.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 009271.python.pyiboot01_bootstrap.line10.comment -----------------------------------------------------------------------------

# 009272.python.pyiboot01_bootstrap.line12.comment -- Start bootstrap process
# 009273.python.pyiboot01_bootstrap.line13.comment Only python built-in modules can be used.

import sys

import pyimod02_importers

# 009274.python.pyiboot01_bootstrap.line19.comment Extend Python import machinery by adding PEP302 importers to sys.meta_path.
pyimod02_importers.install()

# 009275.python.pyiboot01_bootstrap.line22.comment -- Bootstrap process is complete.
# 009276.python.pyiboot01_bootstrap.line23.comment We can use other python modules (e.g. os)

import os  # noqa: E402

# 009278.python.pyiboot01_bootstrap.line27.comment Let other python modules know that the code is running in frozen mode.
if not hasattr(sys, 'frozen'):
    sys.frozen = True

# 009279.python.pyiboot01_bootstrap.line31.comment sys._MEIPASS is now set in the bootloader. Hooray.

# 009280.python.pyiboot01_bootstrap.line33.comment Python 3 C-API function Py_SetPath() resets sys.prefix to empty string. Python 2 was using PYTHONHOME for sys.prefix.
# 009281.python.pyiboot01_bootstrap.line34.comment Let's do the same for Python 3.
sys.prefix = sys._MEIPASS
sys.exec_prefix = sys.prefix

# 009282.python.pyiboot01_bootstrap.line38.comment Python 3.3+ defines also sys.base_prefix. Let's set them too.
sys.base_prefix = sys.prefix
sys.base_exec_prefix = sys.exec_prefix

# 009283.python.pyiboot01_bootstrap.line42.comment Some packages behave differently when running inside virtual environment. E.g., IPython tries to append path
# 009284.python.pyiboot01_bootstrap.line43.comment VIRTUAL_ENV to sys.path. For the frozen app we want to prevent this behavior.
VIRTENV = 'VIRTUAL_ENV'
if VIRTENV in os.environ:
    # 009285.python.pyiboot01_bootstrap.line46.comment On some platforms (e.g., AIX) 'os.unsetenv()' is unavailable and deleting the var from os.environ does not
    # 009286.python.pyiboot01_bootstrap.line47.comment delete it from the environment.
    os.environ[VIRTENV] = ''
    del os.environ[VIRTENV]

# 009287.python.pyiboot01_bootstrap.line51.comment Ensure sys.path contains absolute paths. Otherwise, import of other python modules will fail when current working
# 009288.python.pyiboot01_bootstrap.line52.comment directory is changed by the frozen application.
python_path = []
for pth in sys.path:
    python_path.append(os.path.abspath(pth))
    sys.path = python_path

# 009289.python.pyiboot01_bootstrap.line58.comment At least on Windows, Python seems to hook up the codecs on this import, so it is not enough to just package up all
# 009290.python.pyiboot01_bootstrap.line59.comment the encodings.
# 009291.python.pyiboot01_bootstrap.line60.comment
# 009292.python.pyiboot01_bootstrap.line61.comment It was also reported that without 'encodings' module, the frozen executable fails to load in some configurations:
# 009293.python.pyiboot01_bootstrap.line62.comment http://www.pyinstaller.org/ticket/651
# 009294.python.pyiboot01_bootstrap.line63.comment
# 009295.python.pyiboot01_bootstrap.line64.comment Importing 'encodings' module in a run-time hook is not enough, since some run-time hooks require this module, and the
# 009296.python.pyiboot01_bootstrap.line65.comment order of running the code from the run-time hooks is not defined.
try:
    import encodings  # noqa: F401
except ImportError:
    pass

# 009298.python.pyiboot01_bootstrap.line71.comment In the Python interpreter 'warnings' module is imported when 'sys.warnoptions' is not empty. Mimic this behavior.
if sys.warnoptions:
    import warnings  # noqa: F401

# 009300.python.pyiboot01_bootstrap.line75.comment Install the hooks for ctypes
import pyimod03_ctypes  # noqa: E402

pyimod03_ctypes.install()

# 009302.python.pyiboot01_bootstrap.line80.comment Install the hooks for pywin32 (Windows only)
if sys.platform.startswith('win'):
    import pyimod04_pywin32
    pyimod04_pywin32.install()

# 009303.python.pyiboot01_bootstrap.line85.comment Apply a hack for metadata that was collected from (unzipped) python eggs; the EGG-INFO directories are collected into
# 009304.python.pyiboot01_bootstrap.line86.comment their parent directories (my_package-version.egg/EGG-INFO), and for metadata to be discoverable by
# 009305.python.pyiboot01_bootstrap.line87.comment `importlib.metadata`, the .egg directory needs to be in `sys.path`. The deprecated `pkg_resources` does not have this
# 009306.python.pyiboot01_bootstrap.line88.comment limitation, and seems to work as long as the .egg directory's parent directory (in our case `sys._MEIPASS` is in
# 009307.python.pyiboot01_bootstrap.line89.comment `sys.path`.
for entry in os.listdir(sys._MEIPASS):
    entry = os.path.join(sys._MEIPASS, entry)
    if not os.path.isdir(entry):
        continue
    if entry.endswith('.egg'):
        sys.path.append(entry)
