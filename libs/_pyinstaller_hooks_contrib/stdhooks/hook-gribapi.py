# 013777.python.hook-gribapi.line1.comment ------------------------------------------------------------------
# 013778.python.hook-gribapi.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 013779.python.hook-gribapi.line3.comment
# 013780.python.hook-gribapi.line4.comment This file is distributed under the terms of the GNU General Public
# 013781.python.hook-gribapi.line5.comment License (version 2.0 or later).
# 013782.python.hook-gribapi.line6.comment
# 013783.python.hook-gribapi.line7.comment The full license is available in LICENSE, distributed with
# 013784.python.hook-gribapi.line8.comment this software.
# 013785.python.hook-gribapi.line9.comment
# 013786.python.hook-gribapi.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013787.python.hook-gribapi.line11.comment ------------------------------------------------------------------

import os
import pathlib

from PyInstaller import isolated
from PyInstaller.utils.hooks import collect_data_files, logger

# 013788.python.hook-gribapi.line19.comment Collect the headers (eccodes.h, gribapi.h) that are bundled with the package.
datas = collect_data_files('gribapi')

# 013789.python.hook-gribapi.line22.comment Collect the eccodes shared library. Starting with eccodes 2.37.0, binary wheels with bundled shared library are
# 013790.python.hook-gribapi.line23.comment provided for linux and macOS, and since 2.39.0, also for Windows.


# 013791.python.hook-gribapi.line26.comment NOTE: custom isolated function is used here instead of `get_module_attribute('gribapi.bindings', 'library_path')`
# 013792.python.hook-gribapi.line27.comment hook utility function because with eccodes 2.37.0, `eccodes` needs to be imported before `gribapi` to avoid circular
# 013793.python.hook-gribapi.line28.comment imports... Also, this way, we can obtain the root directory of eccodes package at the same time.
@isolated.decorate
def get_eccodes_library_path():
    import eccodes
    import gribapi.bindings

    return (
        # 013794.python.hook-gribapi.line35.comment Path to eccodes shared library used by the gribapi bindings.
        str(gribapi.bindings.library_path),
        # 013795.python.hook-gribapi.line37.comment Path to eccodes package (implicitly assumed to be next to the gribapi package, since they are part of the
        # 013796.python.hook-gribapi.line38.comment same eccodes dist).
        str(eccodes.__path__[0]),
    )


binaries = []
hiddenimports = []

try:
    library_path, package_path = get_eccodes_library_path()
except Exception:
    logger.warning("hook-gribapi: failed to query gribapi.bindings.library_path!", exc_info=True)
    library_path = None

if library_path:
    if not os.path.isabs(library_path):
        from PyInstaller.depend.utils import _resolveCtypesImports
        resolved_binary = _resolveCtypesImports([os.path.basename(library_path)])
        if resolved_binary:
            library_path = resolved_binary[0][1]
        else:
            logger.warning("hook-gribapi: failed to resolve shared library name %r!", library_path)
            library_path = None
else:
    logger.warning("hook-gribapi: could not determine path to eccodes shared library!")

if library_path:
    # 013797.python.hook-gribapi.line65.comment If we are collecting eccodes shared library that is bundled with eccodes >= 2.37.0 binary wheel, attempt to
    # 013798.python.hook-gribapi.line66.comment preserve its parent directory layout. This ensures that the library is found at run-time, but implicitly requires
    # 013799.python.hook-gribapi.line67.comment PyInstaller 6.x, whose binary dependency analysis (that might also pick up this shared library) also preserves the
    # 013800.python.hook-gribapi.line68.comment parent directory layout of discovered shared libraries. With PyInstaller 5.x, this will result in duplication
    # 013801.python.hook-gribapi.line69.comment because binary dependency analysis collects into top-level application directory, but that copy will not be
    # 013802.python.hook-gribapi.line70.comment discovered at run-time, so duplication is unavoidable.
    library_parent_path = pathlib.PurePath(library_path).parent
    package_parent_path = pathlib.PurePath(package_path).parent

    if package_parent_path in library_parent_path.parents:
        # 013803.python.hook-gribapi.line75.comment Should end up being `eccodes.libs` on Linux, `eccodes/.dylib` on macOS, and `eccodes` on Windows.
        dest_dir = str(library_parent_path.relative_to(package_parent_path))
    else:
        # 013804.python.hook-gribapi.line78.comment External copy; collect into top-level application directory.
        dest_dir = '.'

    logger.info(
        "hook-gribapi: collecting eccodes shared library %r to destination directory %r", library_path, dest_dir
    )
    binaries.append((library_path, dest_dir))

    # 013805.python.hook-gribapi.line86.comment If the shared library is available in the stand-alone `eccodeslib` package, add this package to to hidden imports,
    # 013806.python.hook-gribapi.line87.comment so that `findlibs.find()` can import it and query its `__file__` attribute.
    if 'eccodeslib' in library_parent_path.parts:
        hiddenimports += ['eccodeslib']
