# 008224.python.pyi_rth_gstreamer.line1.comment -----------------------------------------------------------------------------
# 008225.python.pyi_rth_gstreamer.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 008226.python.pyi_rth_gstreamer.line3.comment
# 008227.python.pyi_rth_gstreamer.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 008228.python.pyi_rth_gstreamer.line5.comment you may not use this file except in compliance with the License.
# 008229.python.pyi_rth_gstreamer.line6.comment
# 008230.python.pyi_rth_gstreamer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 008231.python.pyi_rth_gstreamer.line8.comment
# 008232.python.pyi_rth_gstreamer.line9.comment SPDX-License-Identifier: Apache-2.0
# 008233.python.pyi_rth_gstreamer.line10.comment -----------------------------------------------------------------------------


def _pyi_rthook():
    import os
    import sys

    # 008234.python.pyi_rth_gstreamer.line17.comment Without this environment variable set to 'no' importing 'gst' causes 100% CPU load. (Tested on macOS.)
    os.environ['GST_REGISTRY_FORK'] = 'no'

    gst_plugin_paths = [sys._MEIPASS, os.path.join(sys._MEIPASS, 'gst-plugins')]
    os.environ['GST_PLUGIN_PATH'] = os.pathsep.join(gst_plugin_paths)

    # 008235.python.pyi_rth_gstreamer.line23.comment Prevent permission issues on Windows
    os.environ['GST_REGISTRY'] = os.path.join(sys._MEIPASS, 'registry.bin')

    # 008236.python.pyi_rth_gstreamer.line26.comment Only use packaged plugins to prevent GStreamer from crashing when it finds plugins from another version which are
    # 008237.python.pyi_rth_gstreamer.line27.comment installed system wide.
    os.environ['GST_PLUGIN_SYSTEM_PATH'] = ''


_pyi_rthook()
del _pyi_rthook
