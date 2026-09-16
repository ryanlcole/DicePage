# 002799.python.init.line1.comment -----------------------------------------------------------------------------
# 002800.python.init.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 002801.python.init.line3.comment
# 002802.python.init.line4.comment Licensed under the Apache License, Version 2.0 (the "License");
# 002803.python.init.line5.comment you may not use this file except in compliance with the License.
# 002804.python.init.line6.comment
# 002805.python.init.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002806.python.init.line8.comment
# 002807.python.init.line9.comment SPDX-License-Identifier: Apache-2.0
# 002808.python.init.line10.comment -----------------------------------------------------------------------------

import sys
import os

# 002809.python.init.line15.comment A boolean indicating whether the frozen application is a macOS .app bundle.
is_macos_app_bundle = sys.platform == 'darwin' and sys._MEIPASS.endswith("Contents/Frameworks")


def prepend_path_to_environment_variable(path, variable_name):
    """
    Prepend the given path to the list of paths stored in the given environment variable (separated by `os.pathsep`).
    If the given path is already specified in the environment variable, no changes are made. If the environment variable
    is not set or is empty, it is set/overwritten with the given path.
    """
    stored_paths = os.environ.get(variable_name)
    if stored_paths:
        # 002810.python.init.line27.comment If path is already included, make this a no-op. NOTE: we need to split the string and search in the list of
        # 002811.python.init.line28.comment substrings to find an exact match; searching in the original string might erroneously match a prefix of a
        # 002812.python.init.line29.comment longer (i.e., sub-directory) path when such entry already happens to be in PATH (see #8857).
        if path in stored_paths.split(os.pathsep):
            return
        # 002813.python.init.line32.comment Otherwise, prepend the path
        stored_paths = path + os.pathsep + stored_paths
    else:
        stored_paths = path
    os.environ[variable_name] = stored_paths
