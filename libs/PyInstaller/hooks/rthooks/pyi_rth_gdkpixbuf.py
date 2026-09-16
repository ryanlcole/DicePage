# 008177.python.pyi_rth_gdkpixbuf.line1.comment -----------------------------------------------------------------------------
# 008178.python.pyi_rth_gdkpixbuf.line2.comment Copyright (c) 2015-2023, PyInstaller Development Team.
# 008179.python.pyi_rth_gdkpixbuf.line3.comment
# 008180.python.pyi_rth_gdkpixbuf.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008181.python.pyi_rth_gdkpixbuf.line5.comment you may not use this file except in compliance with the License.
# 008182.python.pyi_rth_gdkpixbuf.line6.comment
# 008183.python.pyi_rth_gdkpixbuf.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008184.python.pyi_rth_gdkpixbuf.line8.comment
# 008185.python.pyi_rth_gdkpixbuf.line9.comment SPDX-License-Identifier: Apache-2.0
# 008186.python.pyi_rth_gdkpixbuf.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import atexit
    import os
    import sys
    import tempfile

    pixbuf_file = os.path.join(sys._MEIPASS, 'lib', 'gdk-pixbuf', 'loaders.cache')

    # 008187.python.pyi_rth_gdkpixbuf.line21.comment If we are not on Windows, we need to rewrite the cache -> we rewrite on macOS to support --onefile mode
    if os.path.exists(pixbuf_file) and sys.platform != 'win32':
        with open(pixbuf_file, 'rb') as fp:
            contents = fp.read()

        # 008188.python.pyi_rth_gdkpixbuf.line26.comment Create a temporary file with the cache and cleverly replace the prefix we injected with the actual path.
        fd, pixbuf_file = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as fp:
            libpath = os.path.join(sys._MEIPASS, 'lib').encode('utf-8')
            fp.write(contents.replace(b'@executable_path/lib', libpath))

        try:
            atexit.register(os.unlink, pixbuf_file)
        except OSError:
            pass

    os.environ['GDK_PIXBUF_MODULE_FILE'] = pixbuf_file


_pyi_rthook()
del _pyi_rthook
