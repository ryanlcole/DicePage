# 018180.python.hook-u1db.line1.comment ------------------------------------------------------------------
# 018181.python.hook-u1db.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018182.python.hook-u1db.line3.comment
# 018183.python.hook-u1db.line4.comment This file is distributed under the terms of the GNU General Public
# 018184.python.hook-u1db.line5.comment License (version 2.0 or later).
# 018185.python.hook-u1db.line6.comment
# 018186.python.hook-u1db.line7.comment The full license is available in LICENSE, distributed with
# 018187.python.hook-u1db.line8.comment this software.
# 018188.python.hook-u1db.line9.comment
# 018189.python.hook-u1db.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018190.python.hook-u1db.line11.comment ------------------------------------------------------------------
"""
Pyinstaller hook for u1db module

This hook was tested with:
- u1db 0.1.4 : https://launchpad.net/u1db
- Python 2.7.10
- Linux Debian GNU/Linux unstable (sid)

Test script used for testing:

    import u1db
    db = u1db.open("mydb1.u1db", create=True)
    doc = db.create_doc({"key": "value"}, doc_id="testdoc")
    print doc.content
    print doc.doc_id
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('u1db')
