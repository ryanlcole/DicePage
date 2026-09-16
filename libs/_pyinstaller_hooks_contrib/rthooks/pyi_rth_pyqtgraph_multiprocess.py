# 011599.python.pyi_rth_pyqtgraph_multiprocess.line1.comment -----------------------------------------------------------------------------
# 011600.python.pyi_rth_pyqtgraph_multiprocess.line2.comment Copyright (c) 2022, PyInstaller Development Team.
# 011601.python.pyi_rth_pyqtgraph_multiprocess.line3.comment
# 011602.python.pyi_rth_pyqtgraph_multiprocess.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011603.python.pyi_rth_pyqtgraph_multiprocess.line5.comment
# 011604.python.pyi_rth_pyqtgraph_multiprocess.line6.comment The full license is available in LICENSE, distributed with
# 011605.python.pyi_rth_pyqtgraph_multiprocess.line7.comment this software.
# 011606.python.pyi_rth_pyqtgraph_multiprocess.line8.comment
# 011607.python.pyi_rth_pyqtgraph_multiprocess.line9.comment SPDX-License-Identifier: Apache-2.0
# 011608.python.pyi_rth_pyqtgraph_multiprocess.line10.comment -----------------------------------------------------------------------------

import sys
import os


def _setup_pyqtgraph_multiprocess_hook():
    # 011609.python.pyi_rth_pyqtgraph_multiprocess.line17.comment NOTE: pyqtgraph.multiprocess spawns the sub-process using subprocess.Popen (or equivalent). This means that in
    # 011610.python.pyi_rth_pyqtgraph_multiprocess.line18.comment onefile builds, the executable in subprocess will unpack itself again, into different sys._MEIPASS, because
    # 011611.python.pyi_rth_pyqtgraph_multiprocess.line19.comment the _MEIPASS2 environment variable is not set (bootloader / bootstrap script cleans it up). This will make the
    # 011612.python.pyi_rth_pyqtgraph_multiprocess.line20.comment argv[1] check below fail, due to different sys._MEIPASS value in the subprocess.
    # 011613.python.pyi_rth_pyqtgraph_multiprocess.line21.comment
    # 011614.python.pyi_rth_pyqtgraph_multiprocess.line22.comment To work around this, at the time of writing (PyInstaller 5.5), the user needs to set _MEIPASS2 environment
    # 011615.python.pyi_rth_pyqtgraph_multiprocess.line23.comment variable to sys._MEIPASS before using `pyqtgraph.multiprocess` in onefile builds. And stlib's
    # 011616.python.pyi_rth_pyqtgraph_multiprocess.line24.comment `multiprocessing.freeze_support` needs to be called in the entry-point program, due to `pyqtgraph.multiprocess`
    # 011617.python.pyi_rth_pyqtgraph_multiprocess.line25.comment internally using stdlib's `multiprocessing` primitives.
    if len(sys.argv) == 2 and sys.argv[1] == os.path.join(sys._MEIPASS, 'pyqtgraph', 'multiprocess', 'bootstrap.py'):
        # 011618.python.pyi_rth_pyqtgraph_multiprocess.line27.comment Load as module; this requires --hiddenimport pyqtgraph.multiprocess.bootstrap
        try:
            import importlib.util
            spec = importlib.util.find_spec("pyqtgraph.multiprocess.bootstrap")
            bootstrap_co = spec.loader.get_code("pyqtgraph.multiprocess.bootstrap")
        except Exception:
            bootstrap_co = None

        if bootstrap_co:
            exec(bootstrap_co)
            sys.exit(0)

        # 011619.python.pyi_rth_pyqtgraph_multiprocess.line39.comment Load from file; requires pyqtgraph/multiprocess/bootstrap.py collected as data file
        # 011620.python.pyi_rth_pyqtgraph_multiprocess.line40.comment This is obsolete for PyInstaller >= v6.10.0
        bootstrap_file = os.path.join(sys._MEIPASS, 'pyqtgraph', 'multiprocess', 'bootstrap.py')
        if os.path.isfile(bootstrap_file):
            with open(bootstrap_file, 'r') as fp:
                bootstrap_code = fp.read()
            exec(bootstrap_code)
            sys.exit(0)

        raise RuntimeError("Could not find pyqtgraph.multiprocess bootstrap code or script!")


_setup_pyqtgraph_multiprocess_hook()
del _setup_pyqtgraph_multiprocess_hook
