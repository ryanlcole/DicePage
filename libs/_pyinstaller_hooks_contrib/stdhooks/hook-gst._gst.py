# 013818.python.hook-gst._gst.line1.comment ------------------------------------------------------------------
# 013819.python.hook-gst._gst.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013820.python.hook-gst._gst.line3.comment
# 013821.python.hook-gst._gst.line4.comment This file is distributed under the terms of the GNU General Public
# 013822.python.hook-gst._gst.line5.comment License (version 2.0 or later).
# 013823.python.hook-gst._gst.line6.comment
# 013824.python.hook-gst._gst.line7.comment The full license is available in LICENSE, distributed with
# 013825.python.hook-gst._gst.line8.comment this software.
# 013826.python.hook-gst._gst.line9.comment
# 013827.python.hook-gst._gst.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013828.python.hook-gst._gst.line11.comment ------------------------------------------------------------------

# 013829.python.hook-gst._gst.line13.comment GStreamer contains a lot of plugins. We need to collect them and bundle
# 013830.python.hook-gst._gst.line14.comment them wih the exe file.
# 013831.python.hook-gst._gst.line15.comment We also need to resolve binary dependencies of these GStreamer plugins.

import glob
import os
from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import exec_statement

hiddenimports = ['gmodule', 'gobject']

statement = """
import os
import gst
reg = gst.registry_get_default()
plug = reg.find_plugin('coreelements')
path = plug.get_filename()
print(os.path.dirname(path))
"""

plugin_path = exec_statement(statement)

if is_win:
    # 013832.python.hook-gst._gst.line36.comment TODO Verify that on Windows gst plugins really end with .dll.
    pattern = os.path.join(plugin_path, '*.dll')
else:
    # 013833.python.hook-gst._gst.line39.comment Even on OSX plugins end with '.so'.
    pattern = os.path.join(plugin_path, '*.so')

binaries = [
    (os.path.join('gst_plugins', os.path.basename(f)), f)
    # 013834.python.hook-gst._gst.line44.comment 'f' contains the absolute path
    for f in glob.glob(pattern)]
