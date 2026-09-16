# 020309.python.hook-zmq.line1.comment ------------------------------------------------------------------
# 020310.python.hook-zmq.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020311.python.hook-zmq.line3.comment
# 020312.python.hook-zmq.line4.comment This file is distributed under the terms of the GNU General Public
# 020313.python.hook-zmq.line5.comment License (version 2.0 or later).
# 020314.python.hook-zmq.line6.comment
# 020315.python.hook-zmq.line7.comment The full license is available in LICENSE, distributed with
# 020316.python.hook-zmq.line8.comment this software.
# 020317.python.hook-zmq.line9.comment
# 020318.python.hook-zmq.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020319.python.hook-zmq.line11.comment ------------------------------------------------------------------
"""
Hook for PyZMQ. Cython based Python bindings for messaging library ZeroMQ.
http://www.zeromq.org/
"""
import os
import glob
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import is_module_satisfies, get_module_file_attribute
from PyInstaller.compat import is_win

binaries = []
datas = []
hiddenimports = ['zmq.utils.garbage']

# 020320.python.hook-zmq.line26.comment PyZMQ comes with two backends, cython and cffi. Calling collect_submodules()
# 020321.python.hook-zmq.line27.comment on zmq.backend seems to trigger attempt at compilation of C extension
# 020322.python.hook-zmq.line28.comment module for cffi backend, which will fail if ZeroMQ development files
# 020323.python.hook-zmq.line29.comment are not installed on the system. On non-English locales, the resulting
# 020324.python.hook-zmq.line30.comment localized error messages may cause UnicodeDecodeError. Collecting each
# 020325.python.hook-zmq.line31.comment backend individually, however, does not seem to cause any problems.
hiddenimports += ['zmq.backend']

# 020326.python.hook-zmq.line34.comment cython backend
hiddenimports += collect_submodules('zmq.backend.cython')

# 020327.python.hook-zmq.line37.comment cffi backend: contains extra data that needs to be collected
# 020328.python.hook-zmq.line38.comment (e.g., _cdefs.h)
# 020329.python.hook-zmq.line39.comment
# 020330.python.hook-zmq.line40.comment NOTE: the cffi backend requires compilation of C extension at runtime,
# 020331.python.hook-zmq.line41.comment which appears to be broken in frozen program. So avoid collecting
# 020332.python.hook-zmq.line42.comment it altogether...
if False:
    from PyInstaller.utils.hooks import collect_data_files

    hiddenimports += collect_submodules('zmq.backend.cffi')
    datas += collect_data_files('zmq.backend.cffi', excludes=['**/__pycache__', ])

# 020333.python.hook-zmq.line49.comment Starting with pyzmq 22.0.0, the DLLs in Windows wheel are located in
# 020334.python.hook-zmq.line50.comment site-packages/pyzmq.libs directory along with a .load_order file. This
# 020335.python.hook-zmq.line51.comment file is required on python 3.7 and earlier. On later versions of python,
# 020336.python.hook-zmq.line52.comment the pyzmq.libs is required to exist.
if is_win and is_module_satisfies('pyzmq >= 22.0.0'):
    zmq_root = os.path.dirname(get_module_file_attribute('zmq'))
    libs_dir = os.path.join(zmq_root, os.path.pardir, 'pyzmq.libs')
    # 020337.python.hook-zmq.line56.comment .load_order file (22.0.3 replaced underscore with dash and added
    # 020338.python.hook-zmq.line57.comment version suffix on this file, hence the glob)
    load_order_file = glob.glob(os.path.join(libs_dir, '.load*'))
    datas += [(filename, 'pyzmq.libs') for filename in load_order_file]
    # 020339.python.hook-zmq.line60.comment We need to collect DLLs into _MEIPASS, to avoid duplication due to
    # 020340.python.hook-zmq.line61.comment subsequent binary analysis
    dll_files = glob.glob(os.path.join(libs_dir, "*.dll"))
    binaries += [(dll_file, '.') for dll_file in dll_files]
