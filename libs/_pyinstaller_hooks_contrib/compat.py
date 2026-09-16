# 011409.python.compat.line1.comment ------------------------------------------------------------------
# 011410.python.compat.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 011411.python.compat.line3.comment
# 011412.python.compat.line4.comment This file is distributed under the terms of the GNU General Public
# 011413.python.compat.line5.comment License (version 2.0 or later).
# 011414.python.compat.line6.comment
# 011415.python.compat.line7.comment The full license is available in LICENSE, distributed with
# 011416.python.compat.line8.comment this software.
# 011417.python.compat.line9.comment
# 011418.python.compat.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011419.python.compat.line11.comment ------------------------------------------------------------------

import sys

from PyInstaller.utils.hooks import is_module_satisfies


if is_module_satisfies("PyInstaller >= 6.0"):
    # 011420.python.compat.line19.comment PyInstaller >= 6.0 imports importlib_metadata in its compat module
    from PyInstaller.compat import importlib_metadata
else:
    # 011421.python.compat.line22.comment Older PyInstaller version - duplicate logic from PyInstaller 6.0
    class ImportlibMetadataError(SystemExit):
        def __init__(self):
            super().__init__(
                "pyinstaller-hooks-contrib requires importlib.metadata from python >= 3.10 stdlib or "
                "importlib_metadata from importlib-metadata >= 4.6"
            )

    if sys.version_info >= (3, 10):
        import importlib.metadata as importlib_metadata
    else:
        try:
            import importlib_metadata
        except ImportError as e:
            raise ImportlibMetadataError() from e

        import packaging.version  # For importlib_metadata version check

        # 011423.python.compat.line40.comment Validate the version
        if packaging.version.parse(importlib_metadata.version("importlib-metadata")) < packaging.version.parse("4.6"):
            raise ImportlibMetadataError()
