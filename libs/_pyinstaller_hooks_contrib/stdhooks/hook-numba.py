# 014869.python.hook-numba.line1.comment ------------------------------------------------------------------
# 014870.python.hook-numba.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014871.python.hook-numba.line3.comment
# 014872.python.hook-numba.line4.comment This file is distributed under the terms of the GNU General Public
# 014873.python.hook-numba.line5.comment License (version 2.0 or later).
# 014874.python.hook-numba.line6.comment
# 014875.python.hook-numba.line7.comment The full license is available in LICENSE, distributed with
# 014876.python.hook-numba.line8.comment this software.
# 014877.python.hook-numba.line9.comment
# 014878.python.hook-numba.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014879.python.hook-numba.line11.comment ------------------------------------------------------------------
# 014880.python.hook-numba.line12.comment
# 014881.python.hook-numba.line13.comment NumPy aware dynamic Python compiler using LLVM
# 014882.python.hook-numba.line14.comment https://github.com/numba/numba
# 014883.python.hook-numba.line15.comment
# 014884.python.hook-numba.line16.comment Tested with:
# 014885.python.hook-numba.line17.comment numba 0.26 (Anaconda 4.1.1, Windows), numba 0.28 (Linux)

from PyInstaller.utils.hooks import is_module_satisfies

excludedimports = ["IPython", "scipy"]
hiddenimports = ["llvmlite"]

# 014886.python.hook-numba.line24.comment numba 0.59.0 updated its vendored version of cloudpickle to 3.0.0; this version keeps `cloudpickle_fast` module
# 014887.python.hook-numba.line25.comment around for backward compatibility with existing pickled data, but does not import it directly anymore.
if is_module_satisfies("numba >= 0.59.0"):
    hiddenimports += ["numba.cloudpickle.cloudpickle_fast"]

# 014888.python.hook-numba.line29.comment numba 0.61 introduced new type system with several dynamic redirects using `numba.core.utils._RedirectSubpackage`;
# 014889.python.hook-numba.line30.comment depending on the run-time value of `numba.config.USE_LEGACY_TYPE_SYSTEM`, either "old" or "new" module variant is
# 014890.python.hook-numba.line31.comment loaded. All of these seem to be loaded when `numba` is imported, so there is no need for finer granularity. Also,
# 014891.python.hook-numba.line32.comment as the config value might be manipulated at run-time (e.g., via environment variable), we need to collect both old
# 014892.python.hook-numba.line33.comment and new module variants.
# 014893.python.hook-numba.line34.comment numba 0.62 reverted the change, removing the new type system.
if is_module_satisfies("numba >= 0.61.0rc1, < 0.62.0rc1"):
    # 014894.python.hook-numba.line36.comment NOTE: `numba.core.typing` is also referenced indirectly via `_RedirectSubpackage`, but we do not need a
    # 014895.python.hook-numba.line37.comment hidden import entry for it, because we have entries for its submodules.
    modules_old = [
        'numba.core.datamodel.old_models',
        'numba.core.old_boxing',
        'numba.core.types.old_scalars',
        'numba.core.typing.old_builtins',
        'numba.core.typing.old_cmathdecl',
        'numba.core.typing.old_mathdecl',
        'numba.cpython.old_builtins',
        'numba.cpython.old_hashing',
        'numba.cpython.old_mathimpl',
        'numba.cpython.old_numbers',
        'numba.cpython.old_tupleobj',
        'numba.np.old_arraymath',
        'numba.np.random.old_distributions',
        'numba.np.random.old_random_methods',
    ]
    modules_new = [name.replace('.old_', '.new_') for name in modules_old]
    hiddenimports += modules_old + modules_new
