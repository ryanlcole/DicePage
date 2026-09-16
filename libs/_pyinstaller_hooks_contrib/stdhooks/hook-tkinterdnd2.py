# 017537.python.hook-tkinterdnd2.line1.comment ------------------------------------------------------------------
# 017538.python.hook-tkinterdnd2.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 017539.python.hook-tkinterdnd2.line3.comment
# 017540.python.hook-tkinterdnd2.line4.comment This file is distributed under the terms of the GNU General Public
# 017541.python.hook-tkinterdnd2.line5.comment License (version 2.0 or later).
# 017542.python.hook-tkinterdnd2.line6.comment
# 017543.python.hook-tkinterdnd2.line7.comment The full license is available in LICENSE, distributed with
# 017544.python.hook-tkinterdnd2.line8.comment this software.
# 017545.python.hook-tkinterdnd2.line9.comment
# 017546.python.hook-tkinterdnd2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017547.python.hook-tkinterdnd2.line11.comment ------------------------------------------------------------------

import os
import pathlib
import platform

from PyInstaller.utils.hooks import get_package_paths, logger


# 017548.python.hook-tkinterdnd2.line20.comment tkinterdnd2 contains a tkdnd sub-directory which contains platform-specific directories with shared library and .tcl
# 017549.python.hook-tkinterdnd2.line21.comment files. Collect only the relevant directory, by matching the decision logic from:
# 017550.python.hook-tkinterdnd2.line22.comment https://github.com/Eliav2/tkinterdnd2/blob/9a55907e430234bf8ab72ea614f84af9cc89598c/tkinterdnd2/TkinterDnD.py#L33-L51
def _collect_platform_subdir(system, machine):
    datas = []
    binaries = []

    # 017551.python.hook-tkinterdnd2.line27.comment Under Windows, `platform.machine()` returns the identifier of the *host* architecture, which does not necessarily
    # 017552.python.hook-tkinterdnd2.line28.comment match the architecture of the running process (for example, when running x86 process under x64 Windows, or when
    # 017553.python.hook-tkinterdnd2.line29.comment running either x86 or x64 process under arm64 Windows). The architecture of the running process can be obtained
    # 017554.python.hook-tkinterdnd2.line30.comment from the `PROCESSOR_ARCHITECTURE` environment variable, which is automatically set by Windows / WOW64 subsystem.
    # 017555.python.hook-tkinterdnd2.line31.comment
    # 017556.python.hook-tkinterdnd2.line32.comment NOTE: at the time of writing (tkinterdnd2 v0.4.2), tkinterdnd2 does not account for this, and attempts to load
    # 017557.python.hook-tkinterdnd2.line33.comment the shared library from incorrect directory; as this fails due to architecture mismatch, there is no point in
    # 017558.python.hook-tkinterdnd2.line34.comment us trying to collect that (incorrect) directory.
    if system == "Windows":
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", machine)

    # 017559.python.hook-tkinterdnd2.line38.comment Resolve the platform-specific sub-directory name and shared library suffix.
    DIR_NAMES = {
        "Darwin": {
            "arm64": "osx-arm64",
            "x86_64": "osx-x64",
        },
        "Linux": {
            "aarch64": "linux-arm64",
            "x86_64": "linux-x64",
        },
        "Windows": {
            "ARM64": "win-arm64",
            "AMD64": "win-x64",
            "x86": "win-x86",
        }
    }
    dir_name = DIR_NAMES.get(system, {}).get(machine, None)

    LIB_SUFFICES = {
        "Darwin": "*.dylib",
        "Linux": "*.so",
        "Windows": "*.dll",
    }
    lib_suffix = LIB_SUFFICES.get(system, None)

    if dir_name is None or lib_suffix is None:
        logger.warning(
            "hook-tkinterdnd2: unsupported platform (%s, %s)! Platform-specific directory will not be collected!",
            system, machine
        )
        return datas, binaries

    pkg_base, pkg_dir = get_package_paths("tkinterdnd2")

    dest_dir = os.path.join("tkinterdnd2", "tkdnd", dir_name)
    src_path = pathlib.Path(pkg_dir) / "tkdnd" / dir_name

    if not src_path.is_dir():
        logger.warning("hook-tkinterdnd2: platform-specific sub-directory %r does not exist!", str(src_path))
        return datas, binaries

    # 017560.python.hook-tkinterdnd2.line79.comment Collect the shared library.
    for entry in src_path.glob(lib_suffix):
        binaries.append((str(entry), dest_dir))

    # 017561.python.hook-tkinterdnd2.line83.comment Collect the .tcl files.
    for entry in src_path.glob("*.tcl"):
        datas.append((str(entry), dest_dir))

    return datas, binaries


datas, binaries = _collect_platform_subdir(platform.system(), platform.machine())
