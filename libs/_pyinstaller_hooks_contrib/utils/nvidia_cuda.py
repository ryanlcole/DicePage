# 020355.python.nvidia_cuda.line1.comment ------------------------------------------------------------------
# 020356.python.nvidia_cuda.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 020357.python.nvidia_cuda.line3.comment
# 020358.python.nvidia_cuda.line4.comment This file is distributed under the terms of the GNU General Public
# 020359.python.nvidia_cuda.line5.comment License (version 2.0 or later).
# 020360.python.nvidia_cuda.line6.comment
# 020361.python.nvidia_cuda.line7.comment The full license is available in LICENSE, distributed with
# 020362.python.nvidia_cuda.line8.comment this software.
# 020363.python.nvidia_cuda.line9.comment
# 020364.python.nvidia_cuda.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020365.python.nvidia_cuda.line11.comment ------------------------------------------------------------------

import os
import re

from PyInstaller import compat
from PyInstaller.utils.hooks import (
    logger,
    is_module_satisfies,
)


# 020366.python.nvidia_cuda.line23.comment Helper for collecting shared libraries from NVIDIA CUDA packages on linux.
def collect_nvidia_cuda_binaries(hook_file):
    # 020367.python.nvidia_cuda.line25.comment Find the module underlying this nvidia.something hook; i.e., change ``/path/to/hook-nvidia.something.py`` to
    # 020368.python.nvidia_cuda.line26.comment ``nvidia.something``.
    hook_name, hook_ext = os.path.splitext(os.path.basename(hook_file))
    assert hook_ext.startswith('.py')
    assert hook_name.startswith('hook-')
    module_name = hook_name[5:]

    # 020369.python.nvidia_cuda.line32.comment `search_patterns` was added to `collect_dynamic_libs` in PyInstaller 5.8, so that is the minimum required version.
    binaries = []
    if is_module_satisfies('PyInstaller >= 5.8'):
        from PyInstaller.utils.hooks import collect_dynamic_libs, PY_DYLIB_PATTERNS
        binaries = collect_dynamic_libs(
            module_name,
            # 020370.python.nvidia_cuda.line38.comment Collect fully-versioned .so files (not included in default search patterns).
            search_patterns=PY_DYLIB_PATTERNS + ["lib*.so.*"],
        )
    else:
        logger.warning("hook-%s: this hook requires PyInstaller >= 5.8!", module_name)

    return binaries


# 020371.python.nvidia_cuda.line47.comment Helper to turn list of requirements (e.g., ['nvidia-cublas-cu12', 'nvidia-nccl-cu12', 'nvidia-cudnn-cu12']) into
# 020372.python.nvidia_cuda.line48.comment list of corresponding nvidia.* module names (e.g., ['nvidia.cublas', 'nvidia.nccl', 'nvidia-cudnn']), while ignoring
# 020373.python.nvidia_cuda.line49.comment unrecognized requirements. Intended for use in hooks for frameworks, such as `torch` and `tensorflow`.
def infer_hiddenimports_from_requirements(requirements):
    # 020374.python.nvidia_cuda.line51.comment All nvidia-* packages install to nvidia top-level package, so we cannot query top-level module via
    # 020375.python.nvidia_cuda.line52.comment metadata. Instead, we manually translate them from dist name to package name.
    _PATTERN = r'^nvidia-(?P<subpackage>.+)-cu[\d]+$'
    nvidia_hiddenimports = []

    for req in requirements:
        m = re.match(_PATTERN, req)
        if m is not None:
            # 020376.python.nvidia_cuda.line59.comment Convert
            package_name = "nvidia." + m.group('subpackage').replace('-', '_')
            nvidia_hiddenimports.append(package_name)

    return nvidia_hiddenimports


def create_symlink_suppression_patterns(hook_file):
    hook_name, hook_ext = os.path.splitext(os.path.basename(hook_file))
    assert hook_ext.startswith('.py')
    assert hook_name.startswith('hook-')
    module_name = hook_name[5:]

    # 020377.python.nvidia_cuda.line72.comment Applicable only to Linux
    if not compat.is_linux:
        return []

    # 020378.python.nvidia_cuda.line76.comment Pattern: **/{module_dir}/lib/lib*.so*
    return [os.path.join('**', *module_name.split('.'), 'lib', 'lib*.so*')]
