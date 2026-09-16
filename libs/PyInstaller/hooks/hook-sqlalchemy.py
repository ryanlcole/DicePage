# 006921.python.hook-sqlalchemy.line1.comment -----------------------------------------------------------------------------
# 006922.python.hook-sqlalchemy.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006923.python.hook-sqlalchemy.line3.comment
# 006924.python.hook-sqlalchemy.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006925.python.hook-sqlalchemy.line5.comment or later) with exception for distributing the bootloader.
# 006926.python.hook-sqlalchemy.line6.comment
# 006927.python.hook-sqlalchemy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006928.python.hook-sqlalchemy.line8.comment
# 006929.python.hook-sqlalchemy.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006930.python.hook-sqlalchemy.line10.comment -----------------------------------------------------------------------------

import re
import importlib.util

from PyInstaller import isolated
from PyInstaller.lib.modulegraph.modulegraph import SourceModule
from PyInstaller.utils.hooks import check_requirement, collect_entry_point, logger

datas = []

# 006931.python.hook-sqlalchemy.line21.comment 'sqlalchemy.testing' causes bundling a lot of unnecessary modules.
excludedimports = ['sqlalchemy.testing']

# 006932.python.hook-sqlalchemy.line24.comment Include most common database bindings some database bindings are detected and include some are not. We should
# 006933.python.hook-sqlalchemy.line25.comment explicitly include database backends.
hiddenimports = ['pysqlite2', 'MySQLdb', 'psycopg2', 'sqlalchemy.ext.baked']

if check_requirement('sqlalchemy >= 1.4'):
    hiddenimports.append("sqlalchemy.sql.default_comparator")


@isolated.decorate
def _get_dialect_modules(module_name):
    import importlib
    module = importlib.import_module(module_name)
    return [f"{module_name}.{submodule_name}" for submodule_name in module.__all__]


# 006934.python.hook-sqlalchemy.line39.comment In SQLAlchemy >= 0.6, the "sqlalchemy.dialects" package provides dialects.
# 006935.python.hook-sqlalchemy.line40.comment In SQLAlchemy <= 0.5, the "sqlalchemy.databases" package provides dialects.
if check_requirement('sqlalchemy >= 0.6'):
    hiddenimports += _get_dialect_modules("sqlalchemy.dialects")
else:
    hiddenimports += _get_dialect_modules("sqlalchemy.databases")

# 006936.python.hook-sqlalchemy.line46.comment Collect additional dialects and plugins that are registered via entry-points, under assumption that they are available
# 006937.python.hook-sqlalchemy.line47.comment in the build environment for a reason (i.e., they are used).
for entry_point_name in ('sqlalchemy.dialects', 'sqlalchemy.plugins'):
    ep_datas, ep_hiddenimports = collect_entry_point(entry_point_name)
    datas += ep_datas
    hiddenimports += ep_hiddenimports


def hook(hook_api):
    """
    SQLAlchemy 0.9 introduced the decorator 'util.dependencies'.  This decorator does imports. E.g.:

            @util.dependencies("sqlalchemy.sql.schema")

    This hook scans for included SQLAlchemy modules and then scans those modules for any util.dependencies and marks
    those modules as hidden imports.
    """

    if not check_requirement('sqlalchemy >= 0.9'):
        return

    # 006938.python.hook-sqlalchemy.line67.comment this parser is very simplistic but seems to catch all cases as of V1.1
    depend_regex = re.compile(r'@util.dependencies\([\'"](.*?)[\'"]\)')

    hidden_imports_set = set()
    known_imports = set()
    for node in hook_api.module_graph.iter_graph(start=hook_api.module):
        if isinstance(node, SourceModule) and node.identifier.startswith('sqlalchemy.'):
            known_imports.add(node.identifier)

            # 006939.python.hook-sqlalchemy.line76.comment Read the source...
            with open(node.filename, 'rb') as f:
                source_code = f.read()
            source_code = importlib.util.decode_source(source_code)

            # 006940.python.hook-sqlalchemy.line81.comment ... and scan it
            for match in depend_regex.findall(source_code):
                hidden_imports_set.add(match)

    hidden_imports_set -= known_imports
    if len(hidden_imports_set):
        logger.info("  Found %d sqlalchemy hidden imports", len(hidden_imports_set))
        hook_api.add_imports(*list(hidden_imports_set))
