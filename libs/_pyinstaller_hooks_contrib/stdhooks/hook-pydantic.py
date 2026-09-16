# 015556.python.hook-pydantic.line1.comment ------------------------------------------------------------------
# 015557.python.hook-pydantic.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015558.python.hook-pydantic.line3.comment
# 015559.python.hook-pydantic.line4.comment This file is distributed under the terms of the GNU General Public
# 015560.python.hook-pydantic.line5.comment License (version 2.0 or later).
# 015561.python.hook-pydantic.line6.comment
# 015562.python.hook-pydantic.line7.comment The full license is available in LICENSE, distributed with
# 015563.python.hook-pydantic.line8.comment this software.
# 015564.python.hook-pydantic.line9.comment
# 015565.python.hook-pydantic.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015566.python.hook-pydantic.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import get_module_attribute, collect_submodules
from PyInstaller.utils.hooks import is_module_satisfies

# 015567.python.hook-pydantic.line16.comment By default, PyPi wheels for pydantic < 2.0.0 come with all modules compiled as cython extensions, which prevents
# 015568.python.hook-pydantic.line17.comment PyInstaller from automatically picking up the submodules.
if is_module_satisfies('pydantic >= 2.0.0'):
    # 015569.python.hook-pydantic.line19.comment The `pydantic.compiled` attribute was removed in v2.
    is_compiled = False
else:
    # 015570.python.hook-pydantic.line22.comment NOTE: in PyInstaller 4.x and earlier, get_module_attribute() returns the string representation of the value
    # 015571.python.hook-pydantic.line23.comment ('True'), while in PyInstaller 5.x and later, the actual value is returned (True).
    is_compiled = get_module_attribute('pydantic', 'compiled') in {'True', True}

# 015572.python.hook-pydantic.line26.comment Collect submodules from pydantic; even if the package is not compiled, contemporary versions (2.11.1 at the time
# 015573.python.hook-pydantic.line27.comment of writing) contain redirections and programmatic imports.
hiddenimports = collect_submodules('pydantic')

if is_compiled:
    # 015574.python.hook-pydantic.line31.comment In compiled version, we need to collect the following modules from the standard library.
    hiddenimports += [
        'colorsys',
        'dataclasses',
        'decimal',
        'json',
        'ipaddress',
        'pathlib',
        'uuid',
        # 015575.python.hook-pydantic.line40.comment Optional dependencies.
        'dotenv',
        'email_validator'
    ]
    # 015576.python.hook-pydantic.line44.comment Older releases (prior 1.4) also import distutils.version
    if not is_module_satisfies('pydantic >= 1.4'):
        hiddenimports += ['distutils.version']
    # 015577.python.hook-pydantic.line47.comment Version 1.8.0 introduced additional dependency on typing_extensions
    if is_module_satisfies('pydantic >= 1.8'):
        hiddenimports += ['typing_extensions']
