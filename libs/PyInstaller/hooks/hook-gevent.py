# 005483.python.hook-gevent.line1.comment -----------------------------------------------------------------------------
# 005484.python.hook-gevent.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 005485.python.hook-gevent.line3.comment
# 005486.python.hook-gevent.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005487.python.hook-gevent.line5.comment or later) with exception for distributing the bootloader.
# 005488.python.hook-gevent.line6.comment
# 005489.python.hook-gevent.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005490.python.hook-gevent.line8.comment
# 005491.python.hook-gevent.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005492.python.hook-gevent.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_all, copy_metadata

excludedimports = ["gevent.testing", "gevent.tests"]

datas, binaries, hiddenimports = collect_all(
    'gevent',
    filter_submodules=lambda name: ("gevent.testing" not in name or "gevent.tests" not in name),
    include_py_files=False,
    exclude_datas=["**/tests"]
)

# 005493.python.hook-gevent.line23.comment Gevent uses ``pkg_resources.require("...")``, which means that all its dependencies must also have their metadata.
datas += copy_metadata('gevent', recursive=True)
